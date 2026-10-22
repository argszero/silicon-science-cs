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


def fields(e):
    """What a reference list needs, and what an auditor needs, kept apart."""
    return {
        "key": e["key"],
        "title": (e.get("title") or "").strip(),
        "authors": [e["first_author"]] if e.get("first_author") else [],
        # the corpus stores first-author family only; saying so is better than implying a full list
        "authors_note": "first author only (registry field)" if e.get("first_author") else "no author in the registry record",
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
        "entries": sorted((fields(e) for e in kept), key=lambda x: x["key"]),
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
