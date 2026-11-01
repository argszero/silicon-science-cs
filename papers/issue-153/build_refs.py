"""Issue #153 stage 1: harvest the reference pool for the manuscript, with its search form.

Committed area on purpose.  The previous three rounds ran this work in research/ (git
ignored by design) and two rounds were cut before their work reached git; a stage that is
not committed has not happened.  The pool, its search form and its screening tally live
here, next to the manuscript they serve.

SEARCH FORM (stated so the pool can be re-derived, not just re-used):
  registry : Crossref REST API, https://api.crossref.org/works
  field    : query.bibliographic  (bibliographic query, not a full-text query)
  rows     : 100 per query, 12 queries, relevance order
  window   : from-pub-date 1900-01-01 .. until-pub-date 2026-10-26 (open at the low end)
  scan date: 2026-10-26
  filter   : Crossref type whitelist (journal-article, proceedings-article, book-chapter,
             posted-content, report, book) -- Crossref also returns figure captions, book
             reviews and front matter, which are not references
  screen   : two word sets that must BOTH hit -- a TOPIC term and a SYSTEMS/ALGORITHMS
             domain term.  One set alone admits same-word-different-object records
             (`overlap`, `merge`, `compaction`, `amplification` all have other-field senses,
             and `caching` returns wireless caching-placement papers).

Output: pool.json (every kept record + the search form), screen_tally.txt
"""
import json
import re
import time
import urllib.parse
import urllib.request

SCAN_DATE = "2026-10-26"
WINDOW = "from-pub-date:1900-01-01,until-pub-date:%s" % SCAN_DATE
COLLECTION = "research/papers on log-structured storage compaction and on online "
COLLECTION = "papers on log-structured storage compaction and on online decisions with lookahead"

THEMES = {
    "lsm-compaction": "log-structured merge tree compaction write amplification",
    "levels-tiering": "leveled tiering compaction storage engine",
    "flash-write-amp": "write amplification flash SSD garbage collection",
    "kv-engine": "key-value store storage engine LSM",
    "lookahead-online": "online algorithms lookahead competitive ratio",
    "competitive-paging": "competitive paging caching offline optimal algorithm",
    "mts-kserver": "metrical task systems k-server competitive algorithm",
    "sched-lookahead": "semi-online scheduling lookahead information algorithm",
    "ski-rental": "ski rental online algorithm competitive",
    "logstructured-fs": "log-structured file system cleaning garbage collection",
    "data-placement": "online data placement reorganization cost algorithm",
    "scheduling-theory": "online scheduling competitive ratio algorithm",
}

# Criterion 1: the record names a TOPIC construct.
TOPIC = re.compile(r"(compaction|log[- ]structured|lsm|write amplification|lookahead|look-ahead|"
                   r"ski rental|metrical task|k-server|paging|caching|eviction|tiering|levelled|leveled)", re.I)
# Criterion 2: independently, it names a SYSTEMS or ALGORITHMS domain.  Both must hit.
DOMAIN = re.compile(r"(algorithm|competitive|optimal|bound|online|scheduling|cache|paging|storage|"
                    r"tree|database|file system|flash|ssd|analysis|ratio|memory)", re.I)
GOOD = {"journal-article", "proceedings-article", "book-chapter", "posted-content", "report", "book"}
FIELDS = "title,DOI,issued,type,is-referenced-by-count,container-title,abstract,author"


def fetch(term, rows=100):
    u = ("https://api.crossref.org/works?" + urllib.parse.urlencode(
        {"query.bibliographic": term, "rows": rows, "filter": WINDOW}) + "&select=" + FIELDS)
    r = urllib.request.Request(u, headers={
        "User-Agent": "silicon-science-cs/1.0 (mailto:how2how2how2-arch@example.org)"})
    with urllib.request.urlopen(r, timeout=60) as f:
        return json.load(f)["message"]["items"]


def clean(s):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", s or "")).strip()


def main():
    seen = {}
    tally = []
    fetched_total = 0
    rejected = {"wrong-type": 0, "no-doi-or-title": 0, "topic-only": 0,
                "domain-only": 0, "neither": 0, "duplicate": 0}
    for theme, term in THEMES.items():
        try:
            items = fetch(term)
        except Exception as e:
            tally.append("%-20s ERROR %s" % (theme, e))
            continue
        fetched_total += len(items)
        kept = 0
        for it in items:
            t = clean((it.get("title") or [""])[0])
            if not t or not it.get("DOI"):
                rejected["no-doi-or-title"] += 1
                continue
            if it.get("type") not in GOOD:
                rejected["wrong-type"] += 1
                continue
            tm, dm = bool(TOPIC.search(t)), bool(DOMAIN.search(t))
            if not tm and not dm:
                rejected["neither"] += 1
                continue
            if not tm:
                rejected["domain-only"] += 1
                continue
            if not dm:
                rejected["topic-only"] += 1
                continue
            if it["DOI"] in seen:
                rejected["duplicate"] += 1
                continue
            yr = (it.get("issued", {}).get("date-parts") or [[None]])[0][0]
            seen[it["DOI"]] = dict(
                doi=it["DOI"], title=t, year=yr, theme=theme, type=it.get("type"),
                cited=it.get("is-referenced-by-count", 0),
                venue=clean((it.get("container-title") or [""])[0])[:80],
                abstract=clean(it.get("abstract", ""))[:1600],
                authors=[clean("%s %s" % (a.get("given", ""), a.get("family", "")))
                         for a in (it.get("author") or [])][:6])
            kept += 1
        tally.append("%-20s fetched %3d  kept %3d  (distinct %d)" % (theme, len(items), kept, len(seen)))
        time.sleep(0.3)

    recs = list(seen.values())
    with_abs = [r for r in recs if len(r["abstract"]) >= 120]
    search_form = dict(
        registry="Crossref REST API https://api.crossref.org/works",
        field="query.bibliographic", rows_per_query=100, queries=THEMES,
        window="from-pub-date 1900-01-01 .. until-pub-date %s" % SCAN_DATE,
        scan_date=SCAN_DATE, type_whitelist=sorted(GOOD),
        screen="two word sets, both must hit: TOPIC %s ; DOMAIN %s"
               % (TOPIC.pattern, DOMAIN.pattern))

    body = [
        "POOL TALLY -- issue #153, stage 1 (harvest + screen)",
        "",
        "search form: Crossref query.bibliographic, 100 rows/query, %d queries," % len(THEMES),
        "             window %s, scan date %s" % (WINDOW, SCAN_DATE),
        "",
    ] + tally + [
        "",
        "rows fetched        : %d" % fetched_total,
        "kept (distinct DOI) : %d" % len(recs),
        "rejection tally     : %s" % json.dumps(rejected, sort_keys=True),
        "  rejection rate    : %.1f%% of fetched rows" % (
            100.0 * sum(rejected.values()) / max(1, fetched_total)),
        "with abstract >=120 : %d (%.1f%%)" % (len(with_abs), 100.0 * len(with_abs) / max(1, len(recs))),
        "  -> the other %.1f%% of placement judgements can read only title+venue, which is the"
        % (100.0 - 100.0 * len(with_abs) / max(1, len(recs))),
        "     weaker judgement; the report labels every such placement 'title-only'.",
        "storage themes      : %d" % sum(1 for r in recs if r["theme"] in (
            "lsm-compaction", "levels-tiering", "flash-write-amp", "kv-engine",
            "logstructured-fs", "data-placement")),
        "online themes       : %d" % sum(1 for r in recs if r["theme"] in (
            "lookahead-online", "competitive-paging", "mts-kserver", "sched-lookahead",
            "ski-rental", "scheduling-theory")),
    ]
    txt = "\n".join(body)
    print(txt)
    json.dump(dict(search_form=search_form, records=recs), open("pool.json", "w"), indent=1)
    open("screen_tally.txt", "w").write(txt + "\n")


if __name__ == "__main__":
    main()
