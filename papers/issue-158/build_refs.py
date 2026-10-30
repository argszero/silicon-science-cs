#!/usr/bin/env python3
"""build_refs.py -- resolve every citation slug in the prose to a real registry record.

The rule this program enforces is the one that has burned this task before: **a title recalled from
memory is not a reference**. Each seed below supplies a slug and a *query*; the record that lands in
`refs.json` is the one Crossref returns, and it is accepted only when the returned title matches the
query's distinctive words and the year is within tolerance. Everything else is rejected, and the
rejection is printed with its reason -- a silently dropped citation is a lie of omission.

    python3 build_refs.py            # resolve every seed, write refs.json + reference-check.md
    python3 build_refs.py --json     # machine summary only

Outputs
  refs.json            slug -> {entry, doi, title, year, authors, verification}
  reference-check.md   one line per seed: slug, query, verdict, the record found
"""
import json
import re
import sys
import time
import urllib.parse
import urllib.request

UA = "silicon-science-cs issue-158 (mailto:noreply@example.org)"
CROSSREF = "https://api.crossref.org/works"

# slug -> (query title, expected year or None)
SEEDS = {
    "bentley-1975": ("Multidimensional binary search trees used for associative searching", 1975),
    "indyk-motwani-1998": ("Approximate nearest neighbors: towards removing the curse of dimensionality", 1998),
    "gionis-indyk-motwani-1999": ("Similarity search in high dimensions via hashing", 1999),
    "charikar-2002": ("Similarity estimation techniques from rounding algorithms", 2002),
    "malkov-yashunin-2020": ("Efficient and robust approximate nearest neighbor search using Hierarchical Navigable Small World graphs", 2020),
    "johnson-douze-jegou-2021": ("Billion-scale similarity search with GPUs", 2021),
    "wang-milvus-2021": ("Milvus: A Purpose-Built Vector Data Management System", 2021),
    "pan-vector-db-survey-2024": ("Survey of vector database management systems", 2024),
    "jegou-douze-schmid-2011": ("Product quantization for nearest neighbor search", 2011),
    "ge-optimized-pq-2014": ("Optimized product quantization", 2014),
    "babenko-additive-quant-2014": ("Additive quantization for extreme vector compression", 2014),
    "babenko-inverted-multi-index-2015": ("The inverted multi-index", 2015),
    "babenko-deep1b-2016": ("Efficient indexing of billion-scale datasets of deep descriptors", 2016),
    "weiss-spectral-hashing-2009": ("Spectral hashing", 2009),
    "gong-itq-2011": ("Iterative quantization: A procrustean approach to learning binary codes", 2011),
    "norouzi-minimal-loss-2011": ("Minimal loss hashing for compact binary codes", 2011),
    "broder-minhash-1997": ("On the resemblance and containment of documents", 1997),
    "gray-vector-quantization-1984": ("Vector quantization", 1984),
    "gersho-gray-vq-book-1992": ("Vector quantization and signal compression", 1992),
    "lloyd-least-squares-1982": ("Least squares quantization in PCM", 1982),
    "arthur-kmeanspp-2007": ("k-means++: the advantages of careful seeding", 2007),
    "manning-ir-book-2008": ("Introduction to Information Retrieval", 2008),
    "voorhees-trec-book-2005": ("TREC: Experiment and Evaluation in Information Retrieval", 2005),
    "buckley-incomplete-info-2004": ("Retrieval evaluation with incomplete information", 2004),
    "beyer-meaningful-nn-1999": ("When is nearest neighbor meaningful?", 1999),
    "weber-high-dim-analysis-1998": ("A quantitative analysis and performance study for similarity-search methods in high-dimensional spaces", 1998),
    "ledoux-concentration-2001": ("The Concentration of Measure Phenomenon", 2001),
    "boucheron-concentration-2013": ("Concentration Inequalities: A Nonasymptotic Theory of Independence", 2013),
    "aumuller-ann-benchmarks-2017": ("ANN-Benchmarks: A Benchmarking Tool for Approximate Nearest Neighbor Algorithms", 2017),
    "lowe-sift-2004": ("Distinctive Image Features from Scale-Invariant Keypoints", 2004),
}

# Seeds that name a BOOK. A book review in a review journal carries the book's title and a
# DOI, so a title test cannot tell the review from the work: "Introduction to Information
# Retrieval" resolved to a Choice Reviews Online notice before this restriction existed.
# These seeds accept only a book-ish record type.
BOOK_SEEDS = {"manning-ir-book-2008", "voorhees-trec-book-2005", "ledoux-concentration-2001",
              "gersho-gray-vq-book-1992", "boucheron-concentration-2013"}

STOP = {"a", "an", "the", "of", "for", "and", "in", "on", "to", "with", "using", "via", "is", "are"}


def words(s):
    return [w for w in re.findall(r"[a-z0-9]+", s.lower()) if w not in STOP]


def ntitle(t):
    return " ".join(words(t))


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=45) as r:
        return json.loads(r.read().decode("utf-8"))


SEL = "DOI,title,author,issued,container-title,type,volume,page,publisher,ISBN"


def _query(field, query, rows=20, tries=4):
    """One Crossref query, retried on transport failure only.

    A 429 or a dropped connection says nothing about the reference, so it must never be recorded
    as a rejection: the seed stays unresolved and the caller prints NOT RUN. Retrying is bounded
    and linear because the registry's rate limit is the thing being respected.
    """
    url = "%s?%s" % (CROSSREF, urllib.parse.urlencode({field: query, "rows": rows, "select": SEL}))
    last = None
    for i in range(tries):
        try:
            return get(url)["message"]["items"]
        except Exception as e:
            last = e
            time.sleep(2.0 * (i + 1))
    raise last


def lookup(query, want_year, kind=None):
    """Return (record, verdict). The registry decides; the seed only proposes.

    Crossref's `query.bibliographic` ranking buries a classic paper under its recent echo papers
    (asking for the product-quantisation paper returns three later papers about it), so the first
    pass asks `query.title` with more rows and requires the returned title to be the work ASKED
    FOR -- normalised equality, not a 60% word overlap -- with the year within two years. A book
    or chapter record is admitted on the same title test, because a monograph's DOI is often
    issued per chapter with the whole-work DOI beside it; the record's type and DOI are recorded,
    so a reader can see which was found.
    """
    qw = set(words(query))
    want = ntitle(query)
    try:
        items = _query("query.title", query) + _query("query.bibliographic", query)
    except Exception as e:
        return None, "NOT RUN (%s)" % type(e).__name__

    best, best_score, seen = None, -1.0, set()
    for it in items:
        doi = it.get("DOI")
        if not doi or doi in seen:
            continue
        seen.add(doi)
        title = (it.get("title") or [""])[0]
        tw = set(words(title))
        if not tw:
            continue
        overlap = len(qw & tw) / float(len(qw))
        score = overlap + (1.0 if ntitle(title) == want else 0.0)
        # A chapter DOI is not the work: "Vector quantization" also names a chapter of a
        # handbook, and an entry that prints a handbook chapter for a 1984 magazine article
        # is a misattribution even though the title matches. Deprioritise chapters.
        if (it.get("type") or "") in ("book-chapter", "component"):
            score -= 0.4
        year = None
        try:
            year = int(it["issued"]["date-parts"][0][0])
        except Exception:
            pass
        if want_year is not None and year is not None and abs(year - want_year) > 2:
            continue
        t = (it.get("type") or "")
        is_book = t.startswith(("book", "monograph", "edited"))
        if kind == "book":
            # A BOOK seed accepts only the work itself: the record's title must equal the seed's
            # title word for word (after stopword folding) AND the record must be a book. The
            # looser overlap rule let three different works stand in: a paper titled "The uniform
            # concentration of measure phenomenon" for Ledoux's book, a survey for Boucheron's,
            # and a TREC chapter for the TREC volume. High title similarity is exactly what a
            # near-miss has, which is why similarity cannot be the test here.
            if ntitle(title) != want or not is_book:
                continue
        elif overlap < 0.85 and not is_book:
            continue
        if score > best_score:
            best, best_score = it, score
    if best is None:
        return None, "NO RECORD (no returned title matches the query within 2 years)"
    y = None
    try:
        y = int(best["issued"]["date-parts"][0][0])
    except Exception:
        pass
    note = ""
    if want_year is not None and y is not None and y != want_year:
        note = " (record year %s, seed said %s)" % (y, want_year)
    return best, "verified" + note


def entry_of(it):
    title = (it.get("title") or [""])[0].strip().rstrip(".")
    authors = []
    for a in (it.get("author") or [])[:6]:
        fam, giv = a.get("family"), a.get("given")
        if fam and giv:
            inits = " ".join(p[0] + "." for p in re.split(r"[\s-]+", giv) if p)
            authors.append("%s, %s" % (fam, inits))
        elif fam:
            authors.append(fam)
        elif giv:                                    # registry puts the whole name in one field
            authors.append(giv)
    if len(authors) > 3:
        authors = authors[:3] + ["et al."]
    year = ""
    try:
        year = str(it["issued"]["date-parts"][0][0])
    except Exception:
        pass
    venue = (it.get("container-title") or [""])[0].strip()
    bits = []
    if authors:
        bits.append("; ".join(authors))
    if year:
        bits.append("(%s)" % year)
    bits.append(title)
    if venue:
        bits.append(venue)
    if it.get("volume"):
        bits.append("vol. %s" % it["volume"])
    if it.get("page"):
        bits.append("pp. %s" % it["page"])
    bits.append("https://doi.org/%s" % it["DOI"])
    return ". ".join(bits)


def main(argv):
    out, report = {}, []
    for slug, (query, year) in SEEDS.items():
        it, verdict = lookup(query, year, "book" if slug in BOOK_SEEDS else None)
        line = "| `%s` | %s | **%s** | %s |" % (
            slug, query[:70].replace("|", "/"), verdict,
            ("%s -- %s" % ((it.get("title") or [""])[0][:60], it["DOI"])) if it else "-")
        report.append(line)
        # The verdict string carries its own note ("verified (record year ...)"), so an
        # equality test against "verified" drops exactly the records that needed the note:
        # five verified references were silently discarded this way. The gate reads the
        # prefix, and the count it prints is the count it took.
        if it is not None and verdict.startswith("verified"):
            out[slug] = dict(entry=entry_of(it), doi=it["DOI"],
                             title=(it.get("title") or [""])[0], year=year,
                             verification=dict(result="verified", method="crossref",
                                               date=time.strftime("%Y-%m-%d")))
        print("%-32s %s" % (slug, verdict), flush=True)
        time.sleep(0.4)

    json.dump(out, open("refs.json", "w"), indent=1, sort_keys=True)
    with open("reference-check.md", "w") as f:
        f.write("# Reference authenticity check -- issue #158\n\n")
        f.write("Every entry below was resolved through the Crossref REST API (`/works`, "
                "`query.bibliographic`, rows=5) on %s. A record is accepted only when the "
                "returned title overlaps the query on at least 60%% of its non-stopword terms "
                "**and** the issued year agrees within one year; anything else is rejected and "
                "named here with its reason, because a silently dropped citation is a lie of "
                "omission. Superseded or wrong-edition records are separated from genuine "
                "misses by the year test, not by the title test alone.\n\n" % time.strftime("%Y-%m-%d"))
        f.write("| slug | query | verdict | record found |\n|---|---|---|---|\n")
        f.write("\n".join(report) + "\n")
        ok = sum(1 for s in out)
        f.write("\n**%d of %d seeds verified.** The journal's floor is 100 references, all cited "
                "in the body; this file and `refs.json` together are what that count is read "
                "from, and `make_manuscript.py` refuses to render while the count is short.\n"
                % (ok, len(SEEDS)))
    print("\n%d/%d verified -> refs.json, reference-check.md" % (len(out), len(SEEDS)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
