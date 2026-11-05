#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""harvest_refs.py -- assemble issue #162's reference corpus from registry responses.

The corpus is not written from recollection. What enters it is what Crossref returned for a declared
query, and what survived a screen whose refusals are all recorded with a reason. A reference list a
model produces without looking is exactly the failure this file exists to make impossible: a
plausible title is cheap, a DOI that resolves to that title is not.

Two stages, kept apart because they answer different questions:

  harvest  -- issue each declared query, keep records that pass the type whitelist and the term
              screen, dedup by DOI and by normalised title. Writes candidates with the query that
              found them.
  verify   -- for every candidate, re-fetch `works/<doi>` and corroborate the record by a field that
              is NOT the title's rounded similarity: the first-author family name, or the year when
              no author is asserted. Author mismatch is fatal; a year mismatch is recorded as an
              edition note and the entry stays (a reprint is the same work, a different author is a
              different work).

Refusals are the report. Each refused record carries `reason` and `detail`, and the tally is printed,
because a corpus assembled by deletion is a silent lie unless the deletions are counted.

Usage:
  ./harvest_refs.py --harvest            # query the registry, write refs/candidates.json
  ./harvest_refs.py --verify             # verify candidates, write refs/references.json
  ./harvest_refs.py --report             # print the corpus as markdown, no network
Exit: 0 green, 1 a check failed, 3 NOT RUN (no network / nothing to verify)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import time
import unicodedata
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
REFS = os.path.join(HERE, "refs")
UA = "emrg-silicon-science/1.0 (issue-162 reference verification)"
CROSSREF = "https://api.crossref.org/works"
MAILTO = "emrg@example.invalid"

ROWS = 24
PACE = 0.35

EXIT_OK, EXIT_FAIL, EXIT_NOT_RUN = 0, 1, 3

# Academic types only. Crossref returns figure captions, conference front matter and book reviews
# under the same endpoint, and a corpus padded with those would clear the floor while supporting
# nothing (#149 recorded the same 29-record refusal).
TYPE_OK = {"journal-article", "proceedings-article", "book-chapter", "book", "monograph",
           "reference-entry", "posted-content"}

# The queries. Each is a QAIR: the group it belongs to (which decides where the paper may cite it)
# and the words the returned title must contain at least one of. A query that returns records whose
# titles never mention the group's terms is measuring the registry's recall, not the literature.
QUERIES = [
    # -- the identified set itself: probability inequalities and bounds -------------------------
    ("Frechet bounds joint distribution given marginals", "bounds",
     ("frechet", "fréchet", "marginal", "bounds", "copula", "joint distribution")),
    ("Bonferroni inequalities inclusion exclusion probability bounds", "bounds",
     ("bonferroni", "inclusion", "inequalit", "bounds", "union")),
    ("copula dependence modelling tail dependence", "copula",
     ("copula", "dependence", "tail", "correlat", "multivariate")),
    ("comonotonic countermonotonic bounds sum of risks", "copula",
     ("comonoton", "countermonoton", "bounds", "dependence")),
    ("worst case probability bound no independence assumption", "bounds",
     ("worst", "bound", "independen", "assumption", "distribution")),
    # -- correlated failure in real systems: the prior art the paper must not restate -----------
    ("copysets correlated failures replication data center", "correlated-systems",
     ("copyset", "correlat", "replicat", "failure", "data center")),
    ("correlated failures in large scale storage systems", "correlated-systems",
     ("correlat", "failure", "storage", "large", "cluster")),
    ("correlated disk failures redundancy reliability", "correlated-systems",
     ("correlat", "disk", "failure", "redundan", "reliab")),
    ("datacenter power outage correlated failure availability", "correlated-systems",
     ("power", "outage", "correlat", "failure", "datacenter", "availability")),
    # -- what the quote is made of: durability, availability, nines ------------------------------
    ("erasure coding durability storage reliability analysis", "replication",
     ("erasure", "coding", "durab", "reliab", "storage")),
    ("replication degree availability probability model", "replication",
     ("replicat", "availab", "probab", "model", "redundan")),
    ("mean time to data loss MTTDL disk array", "replication",
     ("mttdl", "mean time", "data loss", "disk", "array", "raid")),
    ("service level agreement availability nines metric", "sla",
     ("sla", "service level", "availab", "nines", "uptime")),
    ("cloud storage durability guarantee measurement", "sla",
     ("durab", "guarantee", "cloud", "storage", "measure")),
    ("quorum loss consensus availability probability", "correlated-systems",
     ("quorum", "availab", "consensus", "loss", "failure")),
    ("redundancy does not imply reliability dependent components", "bounds",
     ("redundan", "reliab", "dependen", "component")),
    # -- the estimand's neighbours: tail quantiles, rare events ---------------------------------
    ("heavy tail rare event probability estimation", "tail",
     ("heavy tail", "rare event", "tail", "extrem")),
    ("extreme value theory rare failure probability", "tail",
     ("extreme", "rare", "failure", "probability", "tail")),
    ("catastrophic risk dependence diversification fallacy", "tail",
     ("catastroph", "risk", "dependen", "diversif", "tail")),
    # -- reporting: what a quoted number identifies --------------------------------------------
    ("statistical reporting uncertainty quoted reliability figures", "reporting",
     ("report", "uncertaint", "reliab", "figure", "quot")),
    ("misuse of probability assumptions reliability engineering", "reporting",
     ("assumption", "probab", "reliab", "engineer", "independen")),
    ("sensitivity analysis assumption dependent probability", "reporting",
     ("sensitiv", "assumption", "dependen", "probab")),
    # -- the canonical systems prior art, named by title because a reviewer will look for it ------
    # Copysets itself (USENIX ATC 2013) carries no Crossref DOI, which is recorded in the report
    # rather than papered over; what IS indexed is the copyset placement literature below.
    ("copyset placement correlated failure data loss model", "correlated-systems",
     ("copyset", "correlat", "placement", "data loss", "model")),
    ("optimal replica placement under correlated failures", "correlated-systems",
     ("replica", "placement", "correlat", "failure", "optimal")),
    ("random versus copyset placement data-loss models proactive", "correlated-systems",
     ("copyset", "data loss", "data-loss", "placement", "model")),
    ("CRUSH controlled scalable decentralized placement replicated data", "replication",
     ("crush", "placement", "replicat", "scalable", "decentral")),
    ("disk failure rates field data large drive population", "correlated-systems",
     ("disk", "failure", "drive", "field", "population", "rate")),
    ("data corruption latent sector errors storage stack analysis", "replication",
     ("corruption", "sector", "latent", "error", "storage", "stack")),
    ("common cause failure redundancy reliability modelling", "bounds",
     ("common cause", "redundan", "reliab", "failure")),
    ("data loss probability model proactive replication repair", "replication",
     ("data loss", "data-loss", "probab", "model", "replicat", "repair")),
]

# Records whose title says nothing this paper uses are refused in pass 2 even when they cleared the
# query's own terms (a shared word naming an adjacent construct is the #155 defect).
FOREIGN = ("climate", "earthquake insurance premium pricing", "credit risk portfolio default",
           "traffic accident", "medical survival transplant", "pharmacokinet",
           "structural engineering bridge", "wind turbine", "hydrolog", "actuarial annuity")


def norm(text):
    """Lower-case, strip accents and punctuation, collapse whitespace."""
    text = unicodedata.normalize("NFKD", text or "")
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = text.lower()
    text = re.sub(r"[^a-z0-9 ]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def words(text):
    return [w for w in norm(text).split() if w]


def get(url, timeout=30):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as fh:
        return json.loads(fh.read().decode("utf-8"))


def q(params):
    return CROSSREF + "?" + urllib.parse.urlencode(params)


def year_of(item):
    for field in ("issued", "published-print", "published-online", "created"):
        parts = (item.get(field) or {}).get("date-parts") or []
        if parts and parts[0] and parts[0][0]:
            return int(parts[0][0])
    return None


def authors_of(item):
    out = []
    for a in item.get("author") or []:
        fam, giv = a.get("family"), a.get("given")
        if fam:
            out.append((fam, giv or ""))
    return out


def slug(author_family, year, title, fallback):
    base = (author_family or fallback or "anon")
    base = re.sub(r"[^A-Za-z]", "", base).lower() or "anon"
    stop = {"the", "a", "an", "of", "on", "in", "for", "and", "to", "with", "is", "not", "what",
            "how", "does", "its", "from", "by"}
    kw = ""
    for w in words(title):
        if w not in stop and len(w) > 2:
            kw = w[:12]
            break
    return "%s%d%s" % (base, year if year else 0, kw)


def harvest():
    if not os.path.isdir(REFS):
        os.makedirs(REFS)
    kept, refused, seen_doi, seen_title = [], [], set(), set()
    for (query, group, terms) in QUERIES:
        url = q({"query.bibliographic": query, "rows": ROWS, "mailto": MAILTO,
                 "select": "DOI,title,author,issued,container-title,type,publisher"})
        try:
            payload = get(url)
        except Exception as exc:                                    # noqa: BLE001
            refused.append({"query": query, "reason": "NOT RUN", "detail": repr(exc)[:120]})
            time.sleep(PACE)
            continue
        items = (payload.get("message") or {}).get("items") or []
        for it in items:
            doi = (it.get("DOI") or "").lower()
            title = " ".join((it.get("title") or [""])[0].split())
            base = {"query": query, "group": group, "doi": doi, "title": title}
            if not doi or not title:
                refused.append(dict(base, reason="no-identifier", detail="missing DOI or title"))
                continue
            if (it.get("type") or "") not in TYPE_OK:
                refused.append(dict(base, reason="type", detail=it.get("type")))
                continue
            y = year_of(it)
            if not y:
                refused.append(dict(base, reason="no-year", detail="no date-parts"))
                continue
            t = norm(title)
            if any(f in t for f in FOREIGN):
                refused.append(dict(base, reason="adjacent-construct",
                                    detail="title names a field this paper does not use"))
                continue
            if not any(term in t for term in terms):
                refused.append(dict(base, reason="terms", detail="no group term in the title"))
                continue
            if doi in seen_doi:
                continue
            key_title = " ".join(words(title))
            if key_title in seen_title:
                refused.append(dict(base, reason="duplicate-title",
                                    detail="same work under another DOI"))
                continue
            auth = authors_of(it)
            seen_doi.add(doi)
            seen_title.add(key_title)
            kept.append({
                "doi": doi,
                "title": title,
                "year": y,
                "type": it.get("type"),
                "venue": " ".join(((it.get("container-title") or [""])[0]).split()),
                "first_family": auth[0][0] if auth else "",
                "first_given": auth[0][1] if auth else "",
                "families": [f for (f, _) in auth],
                "group": group,
                "found_by": query,
            })
        time.sleep(PACE)
    # Keys are assigned after dedup, and a collision is broken by a DOI-derived suffix rather than by
    # arrival order. A counter makes a key an artefact of which query happened to run first: adding a
    # query then silently re-keys records that a placement already cites. The DOI is the record's
    # identity, so the suffix must come from it.
    used = {}
    for rec in kept:
        base = slug(rec["first_family"], rec["year"], rec["title"], rec["doi"].split("/")[1][:8])
        k = base
        if k in used:
            k = "%s-%s" % (base, hashlib.sha1(rec["doi"].encode("utf-8")).hexdigest()[:5])
            while k in used:
                k = k + "x"
        used[k] = 1
        rec["key"] = k
    kept.sort(key=lambda r: r["key"])
    payload = {
        "instrument": "harvest_refs.py",
        "index": "Crossref REST API works endpoint",
        "scan_date": time.strftime("%Y-%m-%d", time.gmtime()),
        "rows_per_query": ROWS,
        "queries": [{"query": a, "group": b, "terms": list(c)} for (a, b, c) in QUERIES],
        "counts": {"harvested": len(kept), "refused": len(refused)},
        "records": kept,
        "refusals": refused,
    }
    path = os.path.join(REFS, "candidates.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=1, sort_keys=True, ensure_ascii=False)
        fh.write("\n")
    print("harvested %d records, refused %d, across %d queries -> %s"
          % (len(kept), len(refused), len(QUERIES), os.path.relpath(path, HERE)))
    tally = {}
    for r in refused:
        tally[r["reason"]] = tally.get(r["reason"], 0) + 1
    for reason, n in sorted(tally.items()):
        print("  refused %-20s %d" % (reason, n))
    if not kept:
        print("NOT RUN: no record passed the screen, so there is no corpus to verify")
        return EXIT_NOT_RUN
    return EXIT_OK


def verify():
    path = os.path.join(REFS, "candidates.json")
    if not os.path.exists(path):
        print("NOT RUN: run --harvest first")
        return EXIT_NOT_RUN
    data = json.load(open(path, encoding="utf-8"))
    recs = data["records"]
    # Carry verification forward. A re-run must never shrink the corpus or re-roll a verdict: a
    # rate-limited or unreachable registry otherwise turns "verified yesterday" into "NOT RUN today",
    # and a corpus that thins on a bad day reads as a finding (the #158 lesson).
    prior = {}
    prev_path = os.path.join(REFS, "references.json")
    if os.path.exists(prev_path):
        for rec in json.load(open(prev_path, encoding="utf-8")).get("records", []):
            if (rec.get("verification") or {}).get("status", "").startswith("verified"):
                prior[rec["doi"].lower()] = rec["verification"]
    checked, failed, carried = [], [], 0
    for rec in recs:
        keep = prior.get(rec["doi"].lower())
        if keep:
            rec["verification"] = keep
            rec["verification"]["carried"] = True
            checked.append(rec["key"])
            carried += 1
            continue
        url = "%s/%s?mailto=%s" % (CROSSREF, urllib.parse.quote(rec["doi"]), MAILTO)
        try:
            item = (get(url).get("message")) or {}
        except Exception as exc:                                    # noqa: BLE001
            rec["verification"] = {"method": "doi", "status": "NOT RUN", "detail": repr(exc)[:120],
                                   "checked_at": time.strftime("%Y-%m-%d", time.gmtime())}
            failed.append((rec["key"], "NOT RUN: " + repr(exc)[:80]))
            time.sleep(PACE)
            continue
        r_title = " ".join((item.get("title") or [""])[0].split())
        r_family = (authors_of(item)[0][0] if authors_of(item) else "")
        r_year = year_of(item)
        # Corroboration must not be the title alone. Both directions of the title check have to
        # hold (the record we stored is the record we asked for), AND an independent field agrees.
        same_title = " ".join(words(r_title)) == " ".join(words(rec["title"]))
        author_ok = (not rec["first_family"]) or (r_family == rec["first_family"])
        year_ok = (r_year == rec["year"])
        status, detail = "verified", []
        if not same_title:
            status = "mismatch"
            detail.append("title differs: %r" % r_title[:80])
        if not author_ok:
            status = "mismatch"
            detail.append("first author %r vs %r" % (r_family, rec["first_family"]))
        if same_title and author_ok and not year_ok:
            status = "verified-edition"
            detail.append("year %r vs %r (edition)" % (r_year, rec["year"]))
        rec["verification"] = {
            "method": "doi",
            "status": status,
            "record_title": r_title,
            "record_first_family": r_family,
            "record_year": r_year,
            "checked_at": time.strftime("%Y-%m-%d", time.gmtime()),
            "detail": "; ".join(detail),
        }
        (checked if status.startswith("verified") else failed).append(
            rec["key"] if status.startswith("verified") else (rec["key"], "; ".join(detail)))
        time.sleep(PACE)
    data["records"] = recs
    data["counts"]["verified"] = len(checked)
    data["counts"]["not_verified"] = len(failed)
    with open(os.path.join(REFS, "references.json"), "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=1, sort_keys=True, ensure_ascii=False)
        fh.write("\n")
    data["counts"]["carried"] = carried
    print("verified %d of %d records (%d carried from a previous run)"
          % (len(checked), len(recs), carried))
    for f in failed[:10]:
        print("  NOT VERIFIED %s -- %s" % f if isinstance(f, tuple) else "  NOT VERIFIED %s" % f)
    if failed:
        print("exit 1: an unverified record must not be cited")
        return EXIT_FAIL
    return EXIT_OK


def report():
    path = os.path.join(REFS, "references.json")
    if not os.path.exists(path):
        print("NOT RUN: run --harvest and --verify first")
        return EXIT_NOT_RUN
    data = json.load(open(path, encoding="utf-8"))
    by_group = {}
    for rec in data["records"]:
        by_group.setdefault(rec["group"], []).append(rec)
    print("corpus: %d records, %d verified" % (len(data["records"]),
                                               data["counts"].get("verified", 0)))
    for g in sorted(by_group):
        print("  %-20s %d" % (g, len(by_group[g])))
    return EXIT_OK


def main(argv=None):
    ap = argparse.ArgumentParser(description="Assemble issue #162's reference corpus.")
    ap.add_argument("--harvest", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--report", action="store_true")
    args = ap.parse_args(argv)
    if args.harvest:
        rc = harvest()
        if rc != EXIT_OK:
            return rc
    if args.verify:
        rc = verify()
        if rc != EXIT_OK:
            return rc
    if args.report:
        return report()
    if not (args.harvest or args.verify or args.report):
        ap.print_help()
        return EXIT_NOT_RUN
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
