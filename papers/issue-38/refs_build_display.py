#!/usr/bin/env python3
"""Build refs_display.json -- the display metadata (authors, year, venue) for issue #38's references.

R3 requires a readable bibliography; `references.json` carries a title, a link and a *stated
difference* per entry but no author field at all, and a publication year for only 18 of 125 entries.

This script merges two things:
  * research/refs_meta_r1.json  -- the bulk harvest (arXiv abs-page citation_* meta tags for the
                                  arXiv entries; the Crossref record for the DOI entries)
  * FILLS below                 -- the five entries whose bulk source carried no author, resolved
                                  individually against a named alternative record

Every entry records `via`, the transport its display metadata came from, so a reader can re-check it.
One entry (51) has no author in any reachable record and is left explicitly unestablished rather than
guessed; `unestablished` records that fact and the manuscript flags it.

Run:  python3 refs_build_display.py
"""
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
META = os.path.join(HERE, "research", "refs_meta_r1.json")
OUT = os.path.join(HERE, "refs_display.json")

# The five entries the bulk harvest could not name, and where the names come from. Each is a
# real external record reached this round; the transport is recorded so the lookup is checkable.
FILLS = {
    "7": {"authors": ["Dlask, Tom\u00e1\u0161", "Savchynskyy, Bogdan"], "year": "2023",
          "via": "openalex title search (api.openalex.org/works?filter=title.search:relative-interior solution); "
                 "arxiv.org/abs/2301.11201 returns HTTP 406 to this client and export.arxiv.org times out"},
    "9": {"authors": ["Alam, Shahriar Tanvir", "Sagor, Eshfar", "Ahmed, Tanjeel", "Haque, Tabassum",
                      "Mahmud, Md Shoaib", "Ibrahim, Salman"], "year": "2023",
          "via": "doi.org landing page citation_author meta tags (the Crossref record for this DOI carries "
                 "no author); year from openalex"},
    "14": {"authors": ["Shapley, Lloyd S.", "Shubik, Mart\u00edn"], "year": "1971", "venue": "RAND Corporation",
           "via": "openalex (the Crossref record is an edited-book entry with no author); rand.org returns 403"},
    "38": {"authors": ["Simon, Herbert Alexander"], "year": "1953", "venue": "RAND Corporation",
           "via": "openalex (the Crossref record is an edited-book entry with no author); the Crossref "
                  "title match 10.2307/1884852 agrees on the author for the same work"},
    "51": {"authors": [], "year": "1997", "unestablished": True,
           "venue": "The Psychology of Attention, The MIT Press",
           "via": "NO AUTHOR ESTABLISHED: Crossref has none for this DOI, OpenAlex returns 0 authorships, "
                  "doi.org and the publisher landing page return 403, Semantic Scholar returns 404. "
                  "Declared on the issue thread rather than guessed."},
}


def initials(given):
    """'Joseph E.' -> 'J. E.' ; 'Herbert Alexander' -> 'H. A.' ; 'E.' -> 'E.'"""
    out = []
    for tok in re.split(r"[\s\-]+", given.strip()):
        tok = tok.strip(". ")
        if not tok:
            continue
        out.append(tok[0].upper() + ".")
    return " ".join(out)


def format_name(raw):
    """Normalise a name to 'Family, I. I.' from either 'Family, Given' or 'Given Family'."""
    s = re.sub(r"\s+", " ", raw.replace("\u00a0", " ")).strip().rstrip(".")
    if not s:
        return ""
    if "," in s:
        fam, giv = s.split(",", 1)
        fam, giv = fam.strip(), giv.strip()
    else:
        parts = s.split(" ")
        if len(parts) == 1:
            return parts[0]
        fam, giv = parts[-1], " ".join(parts[:-1])
    ini = initials(giv)
    return ("%s, %s" % (fam, ini)).strip().rstrip(",") if ini else fam


def main():
    ents = json.load(io.open(os.path.join(HERE, "references.json"), encoding="utf-8"))["entries"]
    meta = json.load(io.open(META, encoding="utf-8"))
    out = {}
    for e in ents:
        k = str(e["key"])
        m = meta.get(k, {})
        raw = [format_name(a) for a in (m.get("authors_raw") or [])]
        year = m.get("year") or ""
        venue = m.get("venue") or e.get("venue") or ""
        via = "arxiv abs page citation_author/citation_date meta tags" if e["source"] == "arxiv" \
            else "crossref api (api.crossref.org/works/<doi>)"
        if k in FILLS:
            f = FILLS[k]
            if f["authors"]:
                raw = [format_name(a) for a in f["authors"]]
            year = f.get("year") or year
            via = f["via"]
        if k in FILLS and FILLS[k].get("venue"):
            venue = FILLS[k]["venue"]
        rec = {"key": e["key"], "authors": [a for a in raw if a], "year": year,
               "venue": venue or ("arXiv preprint arXiv:%s" % e["id"] if e["source"] == "arxiv"
                                  else "doi:%s" % e["id"]),
               "via": via}
        if k in FILLS and FILLS[k].get("unestablished"):
            rec["unestablished"] = True
        out[k] = rec
    io.open(OUT, "w", encoding="utf-8").write(json.dumps(out, indent=1, ensure_ascii=False, sort_keys=True))
    n = len(out)
    noauth = sorted([k for k, v in out.items() if not v["authors"]], key=int)
    noyear = sorted([k for k, v in out.items() if not v["year"]], key=int)
    print("wrote %s: %d entries" % (os.path.basename(OUT), n))
    print("  entries with no author : %d %s" % (len(noauth), noauth))
    print("  entries with no year   : %d %s" % (len(noyear), noyear))
    print("  longest author list    : %d" % max(len(v["authors"]) for v in out.values()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
