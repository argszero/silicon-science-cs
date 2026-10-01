#!/usr/bin/env python3
"""#87 R404 -- verify every entry against the index, and let the instrument prove it can fail.

Two limbs, each read at the registry that owns it:

  * arXiv  -- `id_list` on the export API, in batches, one entry per requested id; the returned title is
              compared with the pooled title the entry's difference line was written against (a mistyped or
              substituted id fails here, which is exactly how two hand-transcribed ids were caught);
  * Crossref -- the DOI's own record, comparing the returned title with the pooled title and reading the
              authors and year the entry prints.

CONTROLS (the instrument must be able to report *absence*, or a run of 169 "verified" is decoration):
  C1  a known-present arXiv id and a known-present DOI are read and reported found;
  C2  a KNOWN-ABSENT arXiv id and a KNOWN-ABSENT DOI are read and must be reported NOT FOUND -- a limb that
      cannot say "no record" has not been tested by its successes;
  C3  the comparison itself is exercised: a deliberately corrupted title is fed to the same matcher and must
      be reported as a MISMATCH.

Writes refs_verified.json (the per-entry verdicts) and reference_check_body.md (the report the package
carries, one line per entry).
"""
import io
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
BUILT = os.path.join(HERE, "refs_built.json")
OUT = os.path.join(HERE, "refs_verified.json")
REPORT = os.path.join(HERE, "reference_check_body.md")
STOP = {"a", "an", "the", "of", "on", "for", "and", "in", "to", "with", "over", "from", "at", "by"}
ATOM = "{http://www.w3.org/2005/Atom}"
ARX = "{http://arxiv.org/schemas/atom}"
SCAN_DATE = "2026-09-21"

CONTROL_ARXIV_PRESENT = "2608.29422"
CONTROL_ARXIV_ABSENT = "2401.99999"
CONTROL_DOI_PRESENT = "10.1093/biomet/6.1.1"
CONTROL_DOI_ABSENT = "10.9999/definitely-not-a-record-r404"


def toks(s):
    return {w for w in re.sub(r"[^a-z0-9]+", " ", (s or "").lower()).split() if w not in STOP}


def same(a, b):
    A, B = toks(a), toks(b)
    return bool(A) and A == B


def fetch(url, tries=3, timeout=60):
    last = None
    for k in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "silicon-science-cs/refverify"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except urllib.error.HTTPError as e:      # a 404 is an ANSWER, not a retry
            if e.code == 404:
                return None
            last = e
            time.sleep(2 + 2 * k)
        except Exception as e:                   # noqa: BLE001
            last = e
            time.sleep(2 + 2 * k)
    raise RuntimeError("fetch failed: %s (%s)" % (url, last))


def arxiv_batch(ids):
    q = ",".join(ids)
    url = ("https://export.arxiv.org/api/query?id_list=" + urllib.parse.quote(q) + "&max_results=%d"
           % (len(ids) + 2))
    xml = fetch(url)
    if xml is None:
        return {}
    root = ET.fromstring(xml)
    out = {}
    for e in root.findall(ATOM + "entry"):
        eid = (e.findtext(ATOM + "id") or "").strip()
        base = eid.rsplit("/abs/", 1)[-1].split("v")[0]
        title = " ".join((e.findtext(ATOM + "title") or "").split())
        if not base or not title or title.lower().startswith("error"):
            continue
        pub = (e.findtext(ATOM + "published") or "").strip()
        out[base] = dict(title=title, year=int(pub[:4]) if pub[:4].isdigit() else None,
                         n_authors=len(e.findall(ATOM + "author")),
                         authors=[(a.findtext(ATOM + "name") or "").strip() for a in e.findall(ATOM + "author")])
    return out


def crossref_one(doi):
    body = fetch("https://api.crossref.org/works/" + urllib.parse.quote(doi))
    if body is None:
        return None
    m = json.loads(body)["message"]
    year = None
    for k in ("published", "issued", "published-print", "published-online", "created"):
        parts = (m.get(k) or {}).get("date-parts") or []
        if parts and parts[0] and parts[0][0]:
            year = parts[0][0]
            break
    return dict(title=" ".join(((m.get("title") or [""])[0] or "").split()), year=year,
                n_authors=len(m.get("author") or []), doi=m.get("DOI", doi),
                venue=" ".join(((m.get("container-title") or [""])[0] or m.get("publisher", "")).split()))


def main():
    built = json.loads(io.open(BUILT, encoding="utf-8").read())
    entries = built["entries"]
    arx = [e for e in entries if e["source"] == "arxiv"]
    dois = [e for e in entries if e["source"] == "crossref"]

    # ---- C1/C2 controls first: a limb that cannot report absence is not a test
    cp = arxiv_batch([CONTROL_ARXIV_PRESENT])
    ca = arxiv_batch([CONTROL_ARXIV_ABSENT])
    dp = crossref_one(CONTROL_DOI_PRESENT)
    da = crossref_one(CONTROL_DOI_ABSENT)
    c3 = dict(corrupted_example=entries[0]["id"], corrupted_ok=not same(entries[0]["pool_title"],
                                                                       entries[0]["pool_title"] + " zzz"))
    controls = dict(
        c1_arxiv_present=dict(id=CONTROL_ARXIV_PRESENT, found=CONTROL_ARXIV_PRESENT in cp),
        c1_doi_present=dict(doi=CONTROL_DOI_PRESENT, found=dp is not None),
        c2_arxiv_absent=dict(id=CONTROL_ARXIV_ABSENT, reported_not_found=CONTROL_ARXIV_ABSENT not in ca),
        c2_doi_absent=dict(doi=CONTROL_DOI_ABSENT, reported_not_found=da is None),
        c3_mismatch_detected=bool(c3["corrupted_ok"]))
    print("controls: arXiv present %s | arXiv absent %s | DOI present %s | DOI absent %s | mismatch detected %s"
          % (controls["c1_arxiv_present"]["found"], controls["c2_arxiv_absent"]["reported_not_found"],
             controls["c1_doi_present"]["found"], controls["c2_doi_absent"]["reported_not_found"],
             controls["c3_mismatch_detected"]), flush=True)

    # ---- arXiv limb, batched
    live = {}
    ids = [e["id"] for e in arx]
    for i in range(0, len(ids), 20):
        chunk = ids[i:i + 20]
        live.update(arxiv_batch(chunk))
        print("   arXiv id_list %d/%d ids read" % (min(i + 20, len(ids)), len(ids)), flush=True)
        time.sleep(3.2)

    rows = []
    for e in arx:
        rec = live.get(e["id"])
        rows.append(dict(key=e["id"], source="arxiv", method="arXiv export API id_list",
                         url=e["url"], found=rec is not None,
                         live_title=(rec or {}).get("title"), live_year=(rec or {}).get("year"),
                         pool_title=e["pool_title"],
                         identity_match=bool(rec) and same(rec["title"], e["pool_title"]),
                         title_equal=bool(rec) and rec["title"].strip() == e["pool_title"].strip(),
                         n_authors_live=(rec or {}).get("n_authors")))
    for j, e in enumerate(dois):
        rec = crossref_one(e["doi"])
        rows.append(dict(key=e["doi"], source="crossref", method="Crossref /works/<doi>",
                         url=e["url"], found=rec is not None,
                         live_title=(rec or {}).get("title"), live_year=(rec or {}).get("year"),
                         pool_title=e["pool_title"],
                         identity_match=bool(rec) and same(rec["title"], e["pool_title"]),
                         title_equal=bool(rec) and rec["title"].strip() == e["pool_title"].strip(),
                         n_authors_live=(rec or {}).get("n_authors")))
        if (j + 1) % 15 == 0:
            print("   Crossref %d/%d DOIs read" % (j + 1, len(dois)), flush=True)
        time.sleep(0.4)

    n_found = sum(1 for r in rows if r["found"])
    n_id = sum(1 for r in rows if r["identity_match"])
    n_eq = sum(1 for r in rows if r["title_equal"])
    bad = [r for r in rows if not r["identity_match"]]
    rep = dict(round="R404", scan_date=SCAN_DATE, n_entries=len(rows), n_found=n_found,
               n_identity_match=n_id, n_title_exact=n_eq, mismatches=bad, controls=controls, rows=rows)
    io.open(OUT, "w", encoding="utf-8").write(json.dumps(rep, indent=1, sort_keys=True))
    print("\nread %d entries: found %d, identity match %d, exact title %d, mismatches %d"
          % (len(rows), n_found, n_id, n_eq, len(bad)))

    # ---- the report the package carries
    lines = ["# Citation authenticity report — issue #87", "",
             "Scan date: **%s**. Every entry below was read at the index that owns it, at the identifier the "
             "entry prints, and the returned record is compared with the title the entry's `Difference:` line "
             "was written against. **The report states the method per entry, the result, and the record "
             "found** — a lookup is not a verification unless the record it returned is the work the entry "
             "names." % SCAN_DATE, "",
             "Instrument: `artefacts/refs/refs_verify_v87.py`. Summary: **%d of %d entries found and "
             "identity-matched** (%d exact-title), **%d mismatches**." % (n_id, len(rows), n_eq, len(bad)), "",
             "## Controls (the instrument can report absence, and its comparison can fail)", "",
             "| control | item | reading |", "|---|---|---|",
             "| C1 known-present arXiv id | `%s` | %s |" % (CONTROL_ARXIV_PRESENT,
                                                            "found" if controls["c1_arxiv_present"]["found"] else "NOT FOUND"),
             "| C1 known-present DOI | `%s` | %s |" % (CONTROL_DOI_PRESENT,
                                                       "found" if controls["c1_doi_present"]["found"] else "NOT FOUND"),
             "| C2 known-absent arXiv id | `%s` | %s |" % (CONTROL_ARXIV_ABSENT,
                                                           "reported NOT FOUND" if controls["c2_arxiv_absent"]["reported_not_found"] else "found (limb cannot report absence)"),
             "| C2 known-absent DOI | `%s` | %s |" % (CONTROL_DOI_ABSENT,
                                                      "reported NOT FOUND" if controls["c2_doi_absent"]["reported_not_found"] else "found (limb cannot report absence)"),
             "| C3 identity comparison | a corrupted title against the same matcher | %s |"
             % ("detected as a mismatch" if controls["c3_mismatch_detected"] else "NOT detected"), "",
             "## Entries", "",
             "Key → method → result → the record found. `[n]` is the manuscript's bibliography key; the "
             "entries are listed in the bibliography's order.", ""]
    for i, (e, r) in enumerate(zip(entries, rows), start=1):
        verdict = ("found; identity match" if r["identity_match"]
                   else ("found; TITLE DIFFERS from the pooled record" if r["found"] else "NOT FOUND"))
        lines.append("[%d] `%s` — %s — **%s** — *%s* (%s). %s" %
                     (i, r["key"], r["method"], verdict,
                      (r["live_title"] or "—")[:120], r["live_year"], r["url"]))
    lines += ["", "## Ambiguity", "",
              "No bracketed group in the manuscript is a numeric range in prose: every `[n]` in the body is a "
              "citation key into this bibliography, so an unmatched bracket would be a defect rather than a "
              "range. The gate's unmatched-bracket advisory is therefore read as a defect.", "",
              "## A note on the two limbs this pipeline retired", "",
              "The first version of the classical limb queried **40 DOIs recalled from memory**: **8 returned "
              "no record**, and **6 that returned one named a different work than the entry claimed** "
              "(`10.1126/science.1058040` was to carry *quantum algorithms* and returns *The Sequence of the "
              "Human Genome*). Those substitutions are recorded as data in `artefacts/refs/refs_form.json`, "
              "and the limb is why every entry here is written from a record the search returned rather than "
              "from an identifier the round remembered.", ""]
    io.open(REPORT, "w", encoding="utf-8").write("\n".join(lines))
    print("wrote %s and %s" % (os.path.basename(OUT), os.path.basename(REPORT)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
