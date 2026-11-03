#!/usr/bin/env python3
"""Issue #155 -- fetch the given names the harvest threw away, once, into a committed cache.

Why this file exists. `build_refs.py:norm()` kept `author[].family` and dropped
`author[].given`, so 92 of the 104 placed records reached the bibliography as a bare
family list (`Kang; Tian; Hu.`) while the renderer's house form is `Family, I.`. The
review of round 2 read that as 82 of 104 entries outside the form and it was right;
the renderer was never the defect -- the record was.

So the repair is a data repair, and it must not make reproduction reach the network.
This program is the ONE step that talks to Crossref, it is NOT run by `reproduce.sh`,
and its output `given_names.json` is committed. `place_refs.py` reads that file; every
run of the package after this one is offline and byte-stable.

Each record stores `family` beside `given` on purpose. The merge in `place_refs.py`
refuses a record whose returned family names do not agree, in order, with the families
the placement already holds: a DOI that resolves to a different author list is not the
same work, and silently rewriting an author component is how a bibliography acquires
an author who never wrote the paper.

Usage:  ./fetch_given.py            fetch what is missing, merge into the cache
        ./fetch_given.py --audit    read the cache and report, never touch the network
"""
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
PLACEMENT = os.path.join(HERE, "placement.json")
OUT = os.path.join(HERE, "given_names.json")
UA = "silicon-science-cs journal package (issue 155) -- author-form repair"
PAUSE = 1.0


def bare_records():
    """Placed records whose author list carries no given name.

    The predicate is imported from `place_refs.py` rather than restated here: the cache has to
    cover exactly the records the placer repairs, and two copies of that question drift.
    """
    from place_refs import needs_given_names
    with open(PLACEMENT, encoding="utf-8") as fh:
        placed = json.load(fh)["placed"]
    return [e for e in placed
            if (e.get("authors") or []) and needs_given_names(e["authors"])]


def fetch(doi, attempts=2):
    url = "https://api.crossref.org/works/" + urllib.parse.quote(doi, safe="")
    for attempt in range(1, attempts + 1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=45) as fh:
                msg = json.load(fh)["message"]
            people = []
            for a in msg.get("author") or []:
                people.append({"given": (a.get("given") or "").strip(),
                               "family": (a.get("family") or a.get("name") or "").strip()})
            return people, None
        except Exception as exc:                                    # noqa: BLE001
            if attempt == attempts:
                return None, "%s: %s" % (type(exc).__name__, exc)
            time.sleep(3)
    return None, "unreachable"


def main():
    if "--audit" in sys.argv[1:]:
        with open(OUT, encoding="utf-8") as fh:
            doc = json.load(fh)
        recs = doc["records"]
        have = sum(1 for r in recs.values() if r["given_names"])
        none = sum(1 for r in recs.values() if not r["given_names"])
        print("given_names.json: %d records read, %d with given names, %d with none in the record"
              % (len(recs), have, none))
        for doi, r in sorted(recs.items()):
            if not r["given_names"]:
                print("   no given name in the record: %s  %s" % (doi, "; ".join(r["family"])))
        return 0

    targets = bare_records()
    print("placed records carrying no given name: %d" % len(targets))
    doc = {"source": "Crossref REST GET /works/<doi>, author objects", "fetched": None,
           "user_agent": UA, "records": {}}
    carried = 0
    if os.path.exists(OUT):
        # A re-run fetches only what the cache does not already hold. Refetching a record this
        # program already read would let one throttled request replace a stored reading with
        # nothing, which is how a cache becomes smaller than the work it describes.
        with open(OUT, encoding="utf-8") as fh:
            old = json.load(fh)
        doc["records"] = dict(old.get("records") or {})
        carried = sum(1 for e in targets if e["doi"] in doc["records"])
        print("already in the cache, carried: %d" % carried)
    failed = []
    for i, e in enumerate(targets, 1):
        if e["doi"] in doc["records"]:
            continue
        people, err = fetch(e["doi"])
        if people is None:
            failed.append({"doi": e["doi"], "error": err})
            print("   ! %3d/%d %s  %s" % (i, len(targets), e["doi"], err))
            continue
        doc["records"][e["doi"]] = {
            "given_names": [p["given"] for p in people],
            "family": [p["family"] for p in people],
            "given": [p["given"] for p in people],
        }
        n_form = sum(1 for g in doc["records"][e["doi"]]["given_names"] if g)
        print("   %3d/%d %s  %d author(s), %d with a given name"
              % (i, len(targets), e["doi"], len(people), n_form))
        time.sleep(PAUSE)

    doc["fetched"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    if failed:
        doc["failed"] = failed
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(doc, indent=1, sort_keys=True) + "\n")
    no_given = sum(1 for r in doc["records"].values()
                   if r["given_names"] and not any(r["given_names"]))
    print("\nwrote %s: %d records (%d with no given name in the record, %d failed)"
          % (os.path.basename(OUT), len(doc["records"]), no_given, len(failed)))
    # A DOI that could not be fetched is not a record without a given name: the first is
    # a gap in this run, the second is a fact about the record. Refuse to hide the first.
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
