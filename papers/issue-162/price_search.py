#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""price_search.py -- was the price of a dependence assumption ever stated as such?

Section 8 of the manuscript used to carry a hedge ("if that pricing is standard somewhere, this paper
is a restatement"). A hedge is a requirement with no collector: nothing in the package could ever fail
because of it. This file is the collector.

WHAT IS SEARCHED FOR. Not "dependence matters" -- that is everywhere. The specific object is a
statement, in the quote's own unit, of what a dependence assumption costs: the dependence that buys
(or costs) one decade of the quoted figure, `rho ~ 9 p^(r-1)` per decade, or any equivalent
formulation of the price (e.g. "the all-fail probability rises by a factor of ten at common-cause
fraction beta = ...").

TWO STAGES, AND THE SECOND IS THE ONE THAT CAN SAY NO.
  * `--harvest` is a MAINTENANCE action: it issues the declared queries against Crossref inside the
    declared window and stores every returned record plus its abstract. Network, not in reproduce.sh.
  * The default run is OFFLINE and is the verdict: it re-applies the declared screen to the stored
    hits, requires a recorded verdict for every record that passes the screen, and prints the tally.
    A record that passes the screen without a verdict is a refusal of the whole step -- a survivor
    cannot be dropped by forgetting to read it.

The screen is a TITLE screen and says so: it decides which records to READ, never what the literature
contains. The verdicts are authored decisions keyed by DOI, for the reason `placements.py` records --
a corpus matched to a claim by vocabulary produces support that does not exist.
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import re
import sys
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "price_search.json")

# The window is part of the claim. Both ends are written, and the harvest is refused if a stored run
# carries a different one -- a search whose window moved is a different search.
WINDOW = "1960-01-01..2026-11-21"
CROSSREF_FROM = "1960-01-01"
CROSSREF_UNTIL = "2026-11-21"

# The declared queries. Adding one here without running `--harvest` makes the offline step red,
# because the stored run is required to answer every query this list names.
QUERIES = [
    ("price", "sensitivity of availability to common cause failures beta factor replication"),
    ("price", "cost of dependence assumption in system reliability prediction"),
    ("price", "effect of assuming independence on predicted unavailability redundant system"),
    ("bounds", "Fréchet bounds availability reliability partially specified marginals"),
    ("bounds", "correlated failure availability replication bound unavailability"),
    ("bounds", "dependent failures quantification reliability redundant systems"),
    ("bounds", "copyset correlated failure replica placement availability"),
    ("beta", "beta factor parametric model common cause failure unavailability redundant group"),
    ("beta", "common cause failure probability estimate alpha beta factor multiple unit"),
    ("nines", "durability nines quoted reliability figure independence assumption"),
]

# A record is READ only if its title names dependence AND a reliability object. This is a screen for
# reading, not a claim about what the field contains; the offline step prints how many it excluded
# so that the number of records the screen never looked at is a printed number too.
DEP = re.compile(r"depend|correlat|common[- ]cause|common mode|coupl|copula|fr[eé]chet|"
                 r"beta[- ]factor|failure domain", re.I)
OBJ = re.compile(r"availab|reliab|unavailab|durab|replica|redundan|fault|loss|failure|"
                 r"bound|schedul", re.I)
# A correction-type record is not the work: it is a notice about one. Recorded here as well as in
# `placements.py` because this file reads titles and would otherwise count an erratum as a candidate.
CORRECTION = re.compile(r"^\s*(erratum|corrigendum|correction|retraction|addendum)\b"
                        r"|\b(erratum|corrigendum|retraction|addendum)\s+to\b"
                        r"|\bcorrection\s+to\b", re.I)

# Verdicts are authored decisions, keyed by DOI. Categories, and what each one asserts:
#   price           states what a dependence assumption costs in the QUOTE'S OWN UNIT -- the
#                   dependence that moves the quoted figure by a decade, rho ~ 9 p^(r-1) -- or an
#                   equivalent pricing of the assumption. This is the only category the question asks
#                   about, and the only one that would make section 8 a restatement.
#   understatement  says the independence assumption makes the multi-unit figure come out too low.
#                   The DIRECTION of the paper's point, with no magnitude and no identified set.
#   model           parameterises the dependence (beta/alpha factor, copula, Markov, common-cause
#                   shock) and computes a figure under that parameter, or estimates the parameter.
#   bounds          states the identified set / the classical bounds for an intersection given
#                   marginals, and does not price an assumption or a quoted figure.
#   design          assumes the dependence and constrains placement so replicas cannot fail together.
#   other           about failures, not about dependence and a quoted figure together.
#
# `basis` records how much of the record was read: `abstract` where one was obtained from Crossref or
# OpenAlex, `title` where none exists in either index. The tally prints both numbers, because "read
# the abstract" and "read the title" are different amounts of evidence and a single count would hide
# which one the empty result rests on.
VERDICTS = {
    "10.1007/978-94-011-3466-8_9": ("bounds", "title", "the Frechet bounds and their applications"),
    "10.1155/jom/4466462": ("model", "abstract", "fits a copula to bivariate lifetimes; no quoted figure priced"),
    "10.1214/lnms/1215452625": ("bounds", "abstract", "review of Frechet bounds and optimal couplings"),
    "10.1007/978-94-017-0629-2_11": ("model", "title", "parametric CCF models for PSA"),
    "10.1016/0026-2714(87)90004-7": ("model", "title", "k-out-of-N:G with CCF and multiple failure modes"),
    "10.1016/j.anucene.2015.12.004": ("model", "title", "CCF unavailability from alpha factors"),
    "10.1109/24.690894": ("model", "abstract", "mixture model fitted to CCF event data"),
    "10.21683/1729-2646-2019-19-2-9-17": ("model", "abstract", "NEAREST: how the computed unavailability moves with the beta parameter, inside the beta model"),
    "10.4271/800631": ("other", "abstract", "qualitative CCF susceptibility analysis"),
    "10.1007/978-94-017-0629-2_6": ("other", "title", "design defences against CCF"),
    "10.1016/0026-2714(94)90111-2": ("model", "title", "2-out-of-n:F with CCF and dependent failure"),
    "10.1016/j.anucene.2013.07.053": ("model", "title", "estimating alpha factors from data"),
    "10.1016/j.ress.2021.107802": ("model", "title", "estimating an inter-unit common-cause probability"),
    "10.1115/1.0000449v": ("model", "title", "inter-unit CCF from intra-unit cases"),
    "10.2172/1835896": ("model", "abstract", "generic priors for alpha factors"),
    "10.31224/6621": ("model", "abstract", "alpha-factor extension; impact stated qualitatively as significant"),
    "10.1007/978-3-319-26626-8_26": ("design", "title", "replica placement under correlated failure"),
    "10.1007/s11227-013-1036-2": ("design", "title", "replica placement for correlated data"),
    "10.1016/j.tcs.2020.01.004": ("design", "title", "optimal replica placement in failure domains"),
    "10.1016/0951-8320(92)90004-5": ("model", "title", "top-event unavailability moments under lognormal correlation"),
    "10.1016/j.engfailanal.2022.106104": ("model", "title", "availability of bogies under correlated failures"),
    "10.1109/ptc.2019.8810845": ("understatement", "abstract", "simultaneous unavailability 'significantly larger' than traditional analysis estimates"),
    "10.1016/0026-2714(77)90342-0": ("other", "title", "system performance and sub-system failure modes"),
    "10.1016/0026-2714(88)90060-1": ("model", "title", "large system under Markov dependence"),
    "10.1109/rams48097.2021.9605735": ("understatement", "abstract", "independence 'does not match engineering practice'; assessment 'may be biased'"),
    "10.1504/ijrs.2016.076345": ("model", "abstract", "Markov model with a repair-dependence function"),
    "10.1016/0026-2714(72)90054-6": ("model", "title", "redundant systems with dependent failures"),
    "10.1016/0026-2714(74)90488-0": ("model", "title", "redundant systems with dependent failures (1974)"),
    "10.1016/0026-2714(81)90294-8": ("model", "title", "multistate redundant systems with CCF and standby"),
    "10.1016/0026-2714(87)90796-7": ("model", "title", "repairable 2-unit parallel with dependent failures"),
    "10.1016/0026-2714(90)90082-x": ("model", "title", "redundant computer systems with CCF"),
    "10.1016/0951-8320(93)90018-t": ("model", "title", "second-moment analysis with dependent failures"),
    "10.1109/tr.1974.5215278": ("model", "abstract", "equivalent-time hazard rates for dependent failures"),
    "10.1016/0143-8174(85)90041-1": ("model", "title", "unavailability with dependent human error"),
    "10.1007/978-3-642-83721-0_12": ("other", "title", "CCF evidence from an operating plant"),
    "10.1016/0026-2714(81)90291-2": ("model", "title", "k-out-of-N availability with CCF and replacement"),
    "10.1016/0026-2714(91)90211-o": ("model", "title", "availability under common-cause shock failures"),
    "10.1016/0026-2714(92)90324-e": ("model", "title", "parallel system with maintenance and CCF"),
    "10.1016/0026-2714(93)90134-k": ("model", "title", "warm standby with CCF"),
    "10.1016/0143-8174(84)90058-1": ("model", "title", "NEAREST: compares beta-factor against multiple-failure-fraction UNITS: the figure, not the price of the assumption"),
    "10.1016/s0026-2714(82)80181-9": ("model", "title", "complex system with shelf-life and CCF"),
    "10.1109/icesp.2014.7347004": ("model", "abstract", "beta-factor model for system unavailability in PSA"),
}

CANNOT = ("a title screen cannot establish an absence, and a title is not an abstract: the verdict is "
          "about the records this file read, at the depth its own tally reports")


def screen(rec):
    t = rec.get("title") or ""
    if CORRECTION.search(t):
        return False, "correction-type record"
    if not DEP.search(t):
        return False, "title names no dependence"
    if not OBJ.search(t):
        return False, "title names no reliability object"
    return True, ""


def harvest():
    hits, run = [], {}
    for group, q in QUERIES:
        url = ("https://api.crossref.org/works?query.bibliographic=" + urllib.parse.quote(q)
               + "&rows=8&select=DOI,title,issued,type,container-title,abstract&filter="
               + urllib.parse.quote("from-pub-date:%s,until-pub-date:%s"
                                    % (CROSSREF_FROM, CROSSREF_UNTIL)))
        try:
            with urllib.request.urlopen(url, timeout=60) as r:
                items = json.load(r)["message"]["items"]
        except Exception as e:                                    # a query that did not run is recorded
            run[q] = {"group": group, "status": "NOT RUN", "detail": repr(e)[:160], "returned": 0}
            continue
        kept = 0
        for it in items:
            title = (it.get("title") or [""])[0]
            if not title:
                continue
            hits.append({
                "doi": it.get("DOI"),
                "title": title,
                "year": (it.get("issued", {}).get("date-parts") or [[None]])[0][0],
                "type": it.get("type"),
                "venue": (it.get("container-title") or [""])[0],
                "abstract": re.sub(r"<[^>]+>", " ", it.get("abstract") or "").strip()[:2400],
                "query": q,
            })
            kept += 1
        run[q] = {"group": group, "status": "ran", "returned": kept}
    # one entry per DOI, keeping the first query that found it
    seen, uniq = set(), []
    for h in hits:
        if h["doi"] in seen:
            continue
        seen.add(h["doi"])
        uniq.append(h)
    doc = {
        "instrument": "price_search.py",
        # WHEN the search was issued, which is not the `window` below: the window is the span of
        # publication dates searched, the timestamp is when the index was asked. Without it a reader
        # cannot tell whether a paper published last month was available to the search, and a later
        # re-run has no baseline to be compared against. `refs/references.json` records `scan_date`
        # for the same reason; this file did not, which made "the search was run" an undated claim.
        "ran_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "question": ("is the price of a dependence assumption -- the dependence that moves the quoted "
                     "figure by one decade, rho ~ 9 p^(r-1) -- stated as such anywhere in the "
                     "reliability or sensitivity literature?"),
        "window": WINDOW,
        "source": "Crossref /works?query.bibliographic (title+abstract index), rows=8 per query",
        "queries": run,
        "records": sorted(uniq, key=lambda r: (r["query"], r["doi"] or "")),
        "screen": "title must name a dependence AND a reliability object; correction-type records refused",
        "caveat": CANNOT,
    }
    json.dump(doc, open(OUT, "w"), indent=1, sort_keys=True)
    print("harvested %d unique records over %d queries -> %s" % (len(uniq), len(QUERIES), OUT))
    for q, v in run.items():
        print("  %-9s %-12s %2d  %s" % (v["status"], v["group"], v["returned"], q[:78]))


def verdict(verbose=True):
    if not os.path.exists(OUT):
        return 3, "price_search.json absent: the search has never been run, so nothing can be reported"
    d = json.load(open(OUT, encoding="utf-8"))
    fails = []
    # An undated search record is refused, so the class cannot come back the way it arrived.
    if not d.get("ran_at"):
        fails.append("the stored search carries no ran_at: a search record that cannot say when it "
                     "ran is an undated claim, and a later re-run has no baseline")
    # The decisions live in VERDICTS, in this file. A copy in the artefact is a second copy that
    # nothing reads and that goes stale the moment a verdict is edited -- the first harvest wrote an
    # EMPTY one because it ran before any verdict was authored, so the artefact said "no verdicts"
    # while the report printed 42. Refusing the key keeps the one-copy rule mechanical.
    if "verdicts" in d:
        fails.append("the stored search carries a `verdicts` copy (%d entries); the decisions live in "
                     "price_search.VERDICTS and a copy in the artefact is a second copy that nothing "
                     "reads" % len(d.get("verdicts") or {}))
    if d.get("window") != WINDOW:
        fails.append("stored window %r != declared %r" % (d.get("window"), WINDOW))
    stored = d.get("queries", {})
    for _group, q in QUERIES:
        got = stored.get(q)
        if got is None:
            fails.append("declared query never run: %s" % q)
        elif got["status"] != "ran":
            fails.append("declared query did not run: %s (%s)" % (q, got.get("detail")))
    verdicts = VERDICTS
    read, unread, excluded = 0, [], 0
    by_cat, by_basis, price = {}, {}, []
    for rec in d.get("records", []):
        ok, why = screen(rec)
        if not ok:
            excluded += 1
            continue
        read += 1
        v = verdicts.get(rec["doi"])
        if not v:
            unread.append(rec["doi"])
            continue
        cat, basis, _why = v
        by_cat[cat] = by_cat.get(cat, 0) + 1
        by_basis[basis] = by_basis.get(basis, 0) + 1
        if cat == "price":
            price.append(rec)
    leg = corpus_leg(verbose=False)
    if leg is not None and leg["unowned"]:
        fails.append("corpus leg surfaced %d title(s) with no verdict: %s"
                     % (len(leg["unowned"]), ", ".join(leg["unowned"][:6])))
    if unread:
        fails.append("%d record(s) passed the screen with no verdict: %s"
                     % (len(unread), ", ".join(unread[:6])))
    if fails:
        for f in fails:
            print("FAIL %s" % f, file=sys.stderr)
        return 1, "%d failure(s)" % len(fails)
    if verbose:
        print("PRICE SEARCH -- run at %s, window %s, source %s"
              % (d.get("ran_at"), d["window"], d.get("source")))
        print("  queries declared %d / ran %d" % (len(QUERIES), len(stored)))
        print("  records stored %d, refused by the screen %d, read %d (every one carries a verdict)"
              % (len(d.get("records", [])), excluded, read))
        print("  read at abstract level %d, at title level only %d"
              % (by_basis.get("abstract", 0), by_basis.get("title", 0)))
        for cat in sorted(by_cat):
            print("    %-14s %d" % (cat, by_cat[cat]))
        t = tally(d)
        print("  statements of the price in the quote's own unit: %d" % t["price"])
        corpus_leg()
        if not price:
            print("  VERDICT: the search was run on the %d queries this file declares, inside %s, and "
                  "came back empty: no record read states what a dependence assumption costs in the "
                  "quote's own unit." % (len(QUERIES), d["window"]))
            under = by_cat.get("understatement", 0)
            print("  WHAT WAS FOUND INSTEAD: %d record(s) state the DIRECTION (independence makes the "
                  "figure come out too low) with no magnitude; %d parameterise the dependence and "
                  "compute a figure under it." % (under, by_cat.get("model", 0)))
            print("  CAVEAT: %s" % d["caveat"])
    return 0, "%d statement(s) of the price" % len(price)


def tally(d):
    """The counts section 8 quotes. One function, so the prose and the print cannot disagree."""
    by_cat, by_basis, excluded, read, why_c = {}, {}, 0, 0, {}
    for rec in d.get("records", []):
        ok, _why = screen(rec)
        if not ok:
            excluded += 1
            why_c[_why] = why_c.get(_why, 0) + 1
            continue
        read += 1
        v = VERDICTS.get(rec["doi"])
        if not v:
            continue
        by_cat[v[0]] = by_cat.get(v[0], 0) + 1
        by_basis[v[1]] = by_basis.get(v[1], 0) + 1
    return {"queries": len(QUERIES), "ran": sum(1 for q, v in d.get("queries", {}).items()
                                                if v.get("status") == "ran"),
            "records": len(d.get("records", [])), "refused": excluded, "read": read,
            "abstract": by_basis.get("abstract", 0), "title": by_basis.get("title", 0),
            "price": by_cat.get("price", 0), "understatement": by_cat.get("understatement", 0),
            "model": by_cat.get("model", 0), "bounds": by_cat.get("bounds", 0),
            "design": by_cat.get("design", 0), "other": by_cat.get("other", 0),
            "refused_no_dependence": why_c.get("title names no dependence", 0),
            "refused_no_object": why_c.get("title names no reliability object", 0),
            "refused_correction": why_c.get("correction-type record", 0)}


CORPUS = os.path.join(HERE, "refs", "references.json")

# Verdicts for the corpus leg, keyed by corpus key. The leg surfaces titles whose words SUGGEST a
# pricing statement; each one is a homonym test, and the test is the paper's own construction. Leaving
# a surfaced title without a verdict here is what the offline step refuses.
CORPUS_VERDICTS = {
    "yeh2017cost": ("other", "'cost' is the allocation objective in money, not the price of a dependence assumption"),
}


def corpus_leg(verbose=True):
    """The corpus this paper already harvested, screened the same way.

    A second source, and a weaker one: the corpus stores titles and venues, not abstracts, so this leg
    can only say which titles ANNOUNCE a pricing statement. It is reported separately from the search
    for that reason -- one number covering both would claim more than either one measured.
    """
    if not os.path.exists(CORPUS):
        return None
    recs = json.load(open(CORPUS, encoding="utf-8"))["records"]
    corr = [r for r in recs if CORRECTION.search(r.get("title") or "")]
    announce = [r for r in recs if DEP.search(r.get("title") or "") and OBJ.search(r.get("title") or "")
                and re.search(r"\b(cost|price|penalt|worth|sensitivit|value of)\b", r.get("title") or "", re.I)]
    unowned = [r["key"] for r in announce if r["key"] not in CORPUS_VERDICTS]
    if verbose:
        print("  CORPUS LEG (%d records already harvested): correction-type titles %d; titles that "
              "announce a pricing statement %d" % (len(recs), len(corr), len(announce)))
        for r in announce:
            v = CORPUS_VERDICTS.get(r["key"])
            print("    announces: %s -- %s" % (r["key"], r["title"][:90]))
            print("      verdict: %s" % (v[1] if v else "NONE -- the leg has no decision on this title"))
    return {"records": len(recs), "correction": len(corr), "announce": len(announce),
            "announce_keys": [r["key"] for r in announce], "unowned": unowned}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--harvest", action="store_true", help="issue the declared queries (network)")
    a = ap.parse_args(argv)
    if a.harvest:
        harvest()
        return 0
    rc, msg = verdict()
    print("PRICE-SEARCH: %s" % msg)
    return rc


if __name__ == "__main__":
    sys.exit(main())
