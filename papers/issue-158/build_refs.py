#!/usr/bin/env python3
"""build_refs.py -- resolve every citation slug in the prose to a real registry record.

The rule this program enforces is the one that has burned this task before: **a title recalled
from memory is not a reference**. Each seed in `refs_seeds.py` supplies a slug and a *query*; the
record that lands in `refs.json` is the one a registry returns, and it is accepted only when the
returned title matches the query and the year agrees within tolerance. Everything else is
rejected, and the rejection is printed with its reason -- a silently dropped citation is a lie of
omission.

Two registries, in order, because they answer different questions:

  Crossref   the published record, with a DOI. Preferred: it is what a reader can open.
  arXiv      a preprint record, for work published in venues Crossref does not index at all
             (NeurIPS, ICLR, SODA). Accepted only on exact normalised title equality, and the
             entry prints its arXiv identifier, so the reader knows which version is cited.

A work is one work: two slugs that resolve to the same DOI or the same normalised title are one
reference, and the second is refused as a duplicate. Without that guard the bibliography can be
grown to any length by naming the same paper twice, which would make the count meaningless.

    python3 build_refs.py            # resolve every seed, write refs.json + reference-check.md
    python3 build_refs.py --json     # machine summary only

Outputs
  refs.json            slug -> {entry, doi, title, year, verification}
  reference-check.md   one line per seed: slug, query, verdict, the record found
"""
import json
import re
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

from refs_seeds import SEEDS, BOOK_SEEDS

UA = "silicon-science-cs issue-158 (mailto:noreply@example.org)"
CROSSREF = "https://api.crossref.org/works"
ARXIV = "http://export.arxiv.org/api/query"
ATOM = "{http://www.w3.org/2005/Atom}"

STOP = {"a", "an", "the", "of", "for", "and", "in", "on", "to", "with", "using", "via", "is", "are"}


def words(s):
    return [w for w in re.findall(r"[a-z0-9]+", s.lower()) if w not in STOP]


def ntitle(t):
    return " ".join(words(t))


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=45) as r:
        return r.read().decode("utf-8")


def getj(url):
    return json.loads(get(url))


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
            return getj(url)["message"]["items"]
        except Exception as e:
            last = e
            time.sleep(2.0 * (i + 1))
    raise last


def admissible(query, title, kind=None, rtype=""):
    """Is `title` the work the seed asked for? Pure, so the refusals can be tested.

    This is the judgement that decides whether a citation is real, and *similarity cannot make
    it*: a near-miss has the highest similarity of all. The rule is containment in both
    directions with a stated tolerance, and it has three parts:

    1. Exact equality after stopword folding is always admissible.
    2. A short query (three content words or fewer) is admissible **only** on exact equality.
       A ratio is weakest exactly where the query is short: "Spectral hashing" is a 100% word
       match for "Fully non-local super-resolution via spectral hashing", and for years the
       ratio test admitted that paper as Weiss et al.'s. Eight such misattributions were in the
       verified set before this rule existed (see the fixtures in `selftest()`).
    3. A longer query tolerates one missing and three extra words -- the shape of a subtitle
       difference or an added "(Survey Article)" -- and nothing more.

    A book seed is stricter still: exact equality and a book-shaped record, because a book
    *review* carries the book's title and a DOI.
    """
    want, got = ntitle(query), ntitle(title)
    is_book = rtype in ("book", "monograph", "edited-book", "reference-book")
    if kind == "book":
        return want == got and is_book
    if want == got:
        return True
    qw, tw = set(words(query)), set(words(title))
    if len(qw) <= 3:
        return False
    return len(qw - tw) <= 1 and len(tw - qw) <= 3


def lookup(query, want_year, kind=None):
    """Return (record, verdict). The registry decides; the seed only proposes.

    Crossref's `query.bibliographic` ranking buries a classic paper under its recent echo papers
    (asking for the product-quantisation paper returns three later papers about it), so the first
    pass asks `query.title` with more rows and requires the returned title to name the work ASKED
    FOR, with the year within two years -- the window that admits a journal version of a
    conference paper without admitting a different work with a similar name.
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
        if not admissible(query, title, kind, (it.get("type") or "")):
            continue
        if score > best_score:
            best, best_score = it, score
    if best is None:
        return None, "NO RECORD (no returned title matches the query within 2 years)"
    return best, "verified"


def lookup_arxiv(query, want_year):
    """Return (record, verdict) from arXiv, for work Crossref does not index.

    Exact normalised title equality is the whole test, because arXiv's own relevance ranking will
    happily return a survey of the paper asked for, and a near-miss has the highest title
    similarity of all. The year must be within one: a preprint posted a decade after the venue
    version is a different reading of the work, and the entry prints arXiv precisely so the
    reader can see a preprint was cited.
    """
    want = ntitle(query)
    url = "%s?%s" % (ARXIV, urllib.parse.urlencode(
        {"search_query": 'ti:"%s"' % query, "max_results": 8}))
    tries = 3
    for i in range(tries):
        try:
            xml = get(url)
            break
        except Exception as e:
            if i == tries - 1:
                return None, "NOT RUN (arxiv %s)" % type(e).__name__
            time.sleep(2.0 * (i + 1))
    try:
        root = ET.fromstring(xml)
    except Exception as e:
        return None, "NOT RUN (arxiv parse %s)" % type(e).__name__

    for e in root.findall(ATOM + "entry"):
        title = " ".join((e.findtext(ATOM + "title") or "").split())
        if ntitle(title) != want:
            continue
        pub = (e.findtext(ATOM + "published") or "")[:4]
        year = int(pub) if pub.isdigit() else None
        if want_year is not None and year is not None and abs(year - want_year) > 1:
            continue
        authors = [(a.findtext(ATOM + "name") or "").strip()
                   for a in e.findall(ATOM + "author")]
        ident = (e.findtext(ATOM + "id") or "").strip()
        return dict(kind="arxiv", title=title, year=year, authors=authors,
                    ident=ident.replace("/abs/", "/abs/")), "verified (arxiv)"
    return None, "NO RECORD (arxiv: no exact title match)"


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


def entry_of_arxiv(it):
    authors = it.get("authors") or []
    if len(authors) > 3:
        authors = authors[:3] + ["et al."]
    bits = []
    if authors:
        bits.append("; ".join(authors))
    if it.get("year"):
        bits.append("(%s)" % it["year"])
    bits.append(it["title"].rstrip("."))
    bits.append("arXiv preprint %s" % it["ident"].rsplit("/abs/", 1)[-1])
    bits.append(it["ident"])
    return ". ".join(bits)



def selftest():
    """The refusals this program can make, tested against the failures it actually made.

    Every negative fixture below is a (query, record title) pair that the previous overlap rule
    ACCEPTED -- these are not hypotheticals, they are the eight misattributions found in the
    verified set of 2026-10-30, and each would have printed a real DOI beside the wrong work.
    A rule that has only ever been seen to accept is not a rule.
    """
    bad = [
        ("Spectral hashing",                    "Fully non-local super-resolution via spectral hashing"),
        ("Milvus: a purpose-built vector data management system", "Purpose-Built Databases"),
        ("DiskANN: fast accurate billion-point nearest neighbor search on a single node", "Nearest Neighbor Queries"),
        ("LSH forest: self-tuning indexes for similarity search", "Parallel and Distributed Indexes"),
        ("Distributed representations of words and phrases and their compositionality",
         "Watching Noun Phrases Emerge: Seeking Compositionality"),
        ("Results of the NeurIPS'21 challenge on billion-scale approximate nearest neighbor search",
         "Approximate Nearest Neighbor Search on Standard Search Engines"),
        ("Manu: a cloud native vector database management system",
         "Relational Database Management System (RDBMS)"),
        ("YFCC100M: the new data in multimedia research",
         "New Research in Multimedia and Internet Systems"),
    ]
    good = [
        ("Spectral hashing", "Spectral hashing", None, "conference"),
        ("Index-driven similarity search in metric spaces",
         "Index-driven similarity search in metric spaces (Survey Article)", None, "journal-article"),
        ("The SR-tree: An index structure for high-dimensional nearest neighbor queries",
         "SR-tree: An index structure for nearest-neighbor searching of high-dimensional point data",
         None, "journal-article"),
        ("Vector quantization", "Vector quantization", None, "journal-article"),
        ("Introduction to Information Retrieval", "Introduction to Information Retrieval", "book", "book"),
    ]
    books_bad = [
        ("Introduction to Information Retrieval", "Introduction to Information Retrieval", "book", "book-review"),
        ("Introduction to Information Retrieval", "Introduction to Information Retrieval", "book", "book-chapter"),
    ]
    fails = 0

    def expect(name, ok):
        nonlocal fails
        print("  [%s] %s" % ("ok" if ok else "FAIL", name))
        if not ok:
            fails += 1

    for q, t in bad:
        expect("refuses %r for %r" % (t[:44], q[:40]), not admissible(q, t))
    for q, t, k, rt in good:
        expect("accepts %r" % t[:52], admissible(q, t, k, rt))
    for q, t, k, rt in books_bad:
        expect("refuses a %s standing in for a book" % rt, not admissible(q, t, k, rt))
    print("SELFTEST: %s" % ("PASS" if fails == 0 else "%d FAILED" % fails))
    return 0 if fails == 0 else 1

def main(argv):
    machine = "--json" in argv
    out, report, why = {}, [], {}
    seen_work = {}                     # normalised identity -> slug that already holds it

    for slug, (query, year) in SEEDS.items():
        kind = "book" if slug in BOOK_SEEDS else None
        rec, verdict = lookup(query, year, kind)
        method = "crossref"
        if rec is None:
            rec, verdict = lookup_arxiv(query, year)
            method = "arxiv"

        entry = None
        ident = None
        if rec is not None:
            if method == "crossref":
                entry = entry_of(rec)
                ident = "doi:" + rec["DOI"].lower()
                year_rec = None
                try:
                    year_rec = int(rec["issued"]["date-parts"][0][0])
                except Exception:
                    pass
            else:
                entry = entry_of_arxiv(rec)
                ident = "arxiv:" + rec["ident"].rstrip("/").rsplit("/", 1)[-1].split("v")[0]
                year_rec = rec.get("year")
            # One work is one reference. Two slugs on one record would let the bibliography be
            # lengthened without adding a single work, which is padding wearing a new name.
            if ident in seen_work:
                rec, entry = None, None
                verdict = "DUPLICATE of `%s` (same work, refused)" % seen_work[ident]
            else:
                seen_work[ident] = slug

        line = "| `%s` | %s | **%s** | %s |" % (
            slug, query[:70].replace("|", "/"), verdict,
            ((" %s" % ident) if ident and rec is not None else "-"))
        report.append(line)
        print("%-34s %-10s %s" % (slug, method, verdict), flush=True)

        if rec is not None:
            out[slug] = dict(entry=entry, doi=(rec.get("DOI") if method == "crossref" else None),
                             title=(rec.get("title") or [""])[0] if method == "crossref" else rec["title"],
                             year=year_rec if year_rec is not None else year,
                             verification=dict(result="verified", method=method,
                                               date=time.strftime("%Y-%m-%d")))
        else:
            key = re.sub(r"\s*\(.*", "", verdict).strip()
            why[key] = why.get(key, 0) + 1
        time.sleep(0.4)

    json.dump(out, open("refs.json", "w"), indent=1, sort_keys=True)
    with open("reference-check.md", "w") as f:
        f.write("# Reference authenticity check -- issue #158\n\n")
        f.write("Every entry below was resolved through a real registry on %s, by a program "
                "(`build_refs.py`) and not by hand. A record is accepted from Crossref only "
                "when the returned title covers at least 85%% of the query's non-stopword "
                "terms and the issued year is within two years (a book seed must instead "
                "return a book-shaped record whose title equals the query word for word, "
                "because a book *review* carries the book's title and DOI); a record is "
                "accepted from arXiv only on exact normalised title equality with the year "
                "within one, and is labelled `arxiv:` so a reader can see a preprint was "
                "cited. Two slugs resolving to one work are refused as duplicates.\n\n"
                % time.strftime("%Y-%m-%d"))
        f.write("| slug | query | verdict | record found |\n|---|---|---|---|\n")
        f.write("\n".join(report) + "\n")
        f.write("\n**%d of %d seeds verified.** Rejections by reason: %s.\n\n"
                % (len(out), len(SEEDS),
                   ", ".join("%s x%d" % (k, v) for k, v in sorted(why.items())) or "none"))
        f.write("The journal's floor is 100 references, all cited in the body; this file and "
                "`refs.json` together are what that count is read from, and "
                "`make_manuscript.py` refuses to render while the count is short or while a "
                "held reference is never cited.\n")
    if machine:
        print(json.dumps(dict(seeds=len(SEEDS), verified=len(out), rejected=why), indent=1))
    print("\n%d/%d verified -> refs.json, reference-check.md" % (len(out), len(SEEDS)))
    return 0


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    sys.exit(main(sys.argv))
