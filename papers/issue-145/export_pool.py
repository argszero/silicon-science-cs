#!/usr/bin/env python3
"""export_pool.py -- freeze the reviewed corpus into the package's citation pool.

The research workspace is git-ignored, so the manuscript cannot resolve its citations against it: a
submitted package must carry the thing its keys resolve to.  This exports the REVIEWED, VERIFIED
entries into `papers/issue-145/refs_pool.json` and records the provenance of that freeze:

  * `source_sha256` -- the corpus file this pool was cut from, so the pool can be audited against it;
  * per entry, the `method` (verified / harvested) and the `query` that produced it, so a reader can
    see the selection rule rather than take the list on trust;
  * the counts of what was excluded, so the pool is not silently smaller than the corpus.

Only `review == "kept"` entries are exported.  An entry still under review is not citable, and the
manuscript's build gate refuses a key the pool does not hold.

Usage: python3 export_pool.py [--out ../refs_pool.json]
"""
import hashlib
import io
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
CORPUS = os.path.join(HERE, "references.json")
# The pool lives beside the manuscript. This script runs both from the research workspace (where the
# corpus is written) and from the package (where the manuscript is), so the output directory is
# chosen by looking for the manuscript rather than assumed from this file's position.
DEFAULT_OUT = os.path.join(
    HERE if os.path.exists(os.path.join(HERE, "manuscript_source.md")) else
    os.path.abspath(os.path.join(HERE, os.pardir)), "refs_pool.json")

# The FULL author list, recovered from Crossref by DOI and committed as a cache so that a
# reproduction is offline (revision round 1, issue #145, required change R1: the list printed one
# author per entry -- 127 of 130 -- because the corpus stores the registry's first-author field, and
# the disclosure of that truncation lived in `reference-check.md` and nowhere in the manuscript).
# `harvest_authors.py` refreshes it; this script only reads it.
AUTHORS = os.path.join(HERE, "authors_by_doi.json")


def author_cache():
    if not os.path.exists(AUTHORS):
        return {}
    with io.open(AUTHORS, encoding="utf-8") as fh:
        return json.load(fh).get("by_doi", {})


def fields(e, cache=None):
    """What a reference list needs, and what an auditor needs, kept apart."""
    cache = cache or {}
    full = (cache.get(e.get("doi") or "") or {}).get("authors") or []
    if full:
        authors, note = full, "full author list, Crossref by DOI (harvest_authors.py)"
    else:
        authors = [e["first_author"]] if e.get("first_author") else []
        note = ("first author only (no DOI in the record)"
                if e.get("first_author") else "no author in the registry record")
    return {
        "key": e["key"],
        "title": (e.get("title") or "").strip(),
        "authors": authors,
        "authors_note": note,
        "year": e.get("year"),
        "venue": (e.get("venue") or "").strip(),
        "type": e.get("type") or "",
        "doi": e.get("doi") or "",
        "url": e.get("url") or "",
        # provenance: how this entry entered the corpus, and under which query
        "method": e.get("method") or "",
        "query": e.get("query") or "",
        "verified_against": "crossref-doi" if e.get("doi") else "none",
    }


def semantic_sha(d):
    """A hash of what the corpus SAYS: every entry's identity, its review verdict and its reason.

    Not a hash of the file: `retrieved_at_utc` and `built_at_utc` are provenance of a networked run,
    and hashing them would make an unchanged set of decisions look like a changed corpus.
    """
    keep = []
    for e in sorted(d["entries"], key=lambda x: x["key"]):
        keep.append([e.get("key"), e.get("title"), e.get("doi"), e.get("year"),
                     e.get("first_author"), e.get("venue"), e.get("type"),
                     e.get("method"), e.get("query"),
                     e.get("review"), e.get("review_reason")])
    blob = json.dumps(keep, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def search_form(d, kept, excluded):
    """The form of the reference search, read off the corpus's own harvest record.

    The bar states three things a related-work search must carry: the **indices**, the **terms**, and
    the **window** -- the last being a coordinate counted on a named date field and written with both
    endpoints, with the **scan date** as a third time.  Two of those are stated here as what was
    actually run rather than as what a form invites, and the awkward one is stated as awkward:

    * `date_filter` records that **no date filter was applied on either endpoint**.  This is the
      honest coordinate: there is no lower bound to name, so the window's only endpoint is the instant
      of the scan, and it is the index's state at that instant rather than a date chosen by the author.
      It is stated as *not applied* -- not as *unavailable*, which would blame the index, and not as a
      window, which would be an invented coordinate.  What bounds the search is therefore **depth**:
      relevance-ranked top-N per query with no pagination, which is recorded beside it.
    * `window.field` names the date field the printed years come FROM (`issued`), because a reader
      checking whether the search could have seen a cited work needs to know which date it would have
      been ranked and dated by.
    """
    h = d.get("harvest") or {}
    per_query = h.get("per_query") or {}
    years = sorted(e["year"] for e in kept if e.get("year"))
    scan = d.get("built_at_utc")
    return {
        "index": "Crossref REST API, https://api.crossref.org/works",
        "query_field": "query.bibliographic (free-text bibliographic relevance query)",
        "date_filter": "none applied: neither endpoint was restricted",
        "depth": "relevance-ranked, top rows_per_query per query, no pagination",
        # Two populations, named so neither can be read as the other: the queries the harvest BLOCK
        # records (one run's table, whose per-query `kept` sums to that run's additions), and the
        # queries that actually produced an entry this pool cites (the corpus accumulates across runs,
        # so a query kept at 0 in the recorded run can still be the source of entries a later run of
        # the same query id returned).
        "queries_recorded": len(per_query),
        "queries_yielding_a_cited_entry": len(set(e["query"] for e in kept if e.get("query"))),
        "rows_per_query": h.get("rows_per_query"),
        "rows_returned_in_recorded_run": sum(v.get("returned", 0) for v in per_query.values()),
        "kept_in_recorded_run": sum(v.get("kept", 0) for v in per_query.values()),
        "queries_failed_in_recorded_run": len(h.get("failed_queries") or []),
        "set_aside_in_recorded_run": dict((k, v) for k, v in sorted(h.items())
                                          if k.startswith("skipped_")),
        "scan_at_utc": scan,
        "window": {"field": "Crossref issued (the year each entry prints)",
                   "from": None, "to": scan},
        "kept_year_span": [years[0], years[-1]] if years else None,
        "corpus_considered": len(kept) + len(excluded),
    }


def main():
    out_path = DEFAULT_OUT
    if "--out" in sys.argv:
        out_path = sys.argv[sys.argv.index("--out") + 1]
    raw = io.open(CORPUS, "rb").read()
    d = json.loads(raw)
    entries = d["entries"]
    kept = [e for e in entries if e.get("review", "kept") == "kept"]
    excluded = [e for e in entries if e.get("review") == "excluded"]

    for e in kept:
        if not e.get("doi"):
            print("FAIL: kept entry without a DOI has no locator: %s" % e["key"])
            return 1
        if not e.get("title"):
            print("FAIL: kept entry without a title: %s" % e["key"])
            return 1

    cache = author_cache()
    if not cache:
        print("NOTE: no %s -- the list will print one author per entry and say so"
              % os.path.basename(AUTHORS))
    pool = {
        # No wall clock, and the pin is over the SEMANTIC content rather than the file's bytes:
        # a timestamp inside the corpus (or in this header) would make the pool a different file on
        # every run, and a pool that changes when nothing changed cannot be compared byte-for-byte.
        "source": "papers/issue-145/research/references.json",
        "source_content_sha256": semantic_sha(d),
        "counts": {
            "corpus_entries": len(entries),
            "kept": len(kept),
            "excluded": len(excluded),
            "verified": sum(1 for e in kept if not e.get("query")),
            "harvested": sum(1 for e in kept if e.get("query")),
        },
        "how_built": ("grown from Crossref returns for topic queries, then reviewed twice: a salience "
                      "pass (a title obviously in another field) and a criterion pass organised by "
                      "this paper's constructs (does the record name a mechanism, population or "
                      "method the paper uses?). Every kept entry carries the query that produced it; "
                      "refusals stay in the corpus with a reason and are counted, not deleted."),
        # THE SEARCH'S FORM, which the submission bar asks a related-work search to carry: the
        # indices, the terms and the window -- the window being a COORDINATE on a named date field,
        # never a word.  It is frozen here, at export, because the report that prints it must remain a
        # function of the committed package: a report that read the corpus's harvest block at report
        # time could not be regenerated in a checkout that does not carry the research workspace.
        "search_form": search_form(d, kept, excluded),
        "entries": sorted((fields(e, cache) for e in kept), key=lambda x: x["key"]),
    }
    io.open(out_path, "w", encoding="utf-8").write(json.dumps(pool, indent=1, sort_keys=True) + "\n")
    print("wrote %s" % out_path)
    print("  %d entries: %d verified + %d harvested (%d excluded, not exported)"
          % (len(kept), pool["counts"]["verified"], pool["counts"]["harvested"], len(excluded)))
    print("  source_content_sha256 %s" % pool["source_content_sha256"][:32])
    nodate = [e["key"] for e in kept if not e.get("year")]
    noauth = [e["key"] for e in kept if not e.get("first_author")]
    print("  incomplete metadata: %d without a year, %d without an author" % (len(nodate), len(noauth)))
    for k in nodate + noauth:
        print("    - %s" % k)
    return 0


if __name__ == "__main__":
    sys.exit(main())
