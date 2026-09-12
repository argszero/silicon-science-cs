#!/usr/bin/env python3
"""Bibliography builder for issue #1.

Two stages, both driven by live API responses so that reference-check.md is a
report of what was actually retrieved rather than a hand-written claim:

    harvest  -> search arXiv (by term, by category) and Crossref (bibliographic
                query) and store every candidate with the record the API returned
    verify   -> re-fetch each SELECTED entry by its own identifier, compare the
                returned title against the title recorded in the selection, and
                write references.json plus the reference-check.md report lines

Usage:
    python3 refs_tool.py harvest
    python3 refs_tool.py verify

Only the Python 3 standard library is used. Network endpoints:
    arXiv   https://export.arxiv.org/api/query   (https only; http 301s)
    Crossref https://api.crossref.org/works      (mailto= enters the polite pool)
"""
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
CAND = os.path.join(HERE, "refs_candidates.json")
SEL = os.path.join(HERE, "refs_selected.json")
OUT = os.path.join(HERE, "references.json")
UA = "silicon-science-cs-issue1/1.0 (mailto:how2how2how2-arch@users.noreply.github.com)"
ARXIV = "https://export.arxiv.org/api/query?"
CROSSREF = "https://api.crossref.org/works"
SLEEP_ARXIV = 3.2
SLEEP_CROSSREF = 1.2


def fetch(url, tries=3):
    last = None
    for k in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=45) as fh:
                return fh.read().decode("utf-8", "replace")
        except Exception as exc:          # network hiccup, rate limit, 5xx
            last = exc
            time.sleep(4.0 * (k + 1))
    print("    fetch failed: %s" % last)
    return None


def norm(s):
    s = re.sub(r"\s+", " ", s or "").strip().lower()
    s = re.sub(r"[^a-z0-9 ]+", "", s)
    return s


def flat(s):
    return re.sub(r"\s+", " ", s or "").strip()


def arxiv_entries(xml):
    out = []
    for e in re.findall(r"<entry>(.*?)</entry>", xml or "", re.S):
        def g(tag):
            m = re.search(r"<%s>(.*?)</%s>" % (tag, tag), e, re.S)
            return flat(m.group(1)) if m else ""
        link = g("id")
        m = re.search(r"arxiv.org/abs/([^v\s]+)", link)
        out.append({
            "source": "arxiv",
            "id": m.group(1) if m else "",
            "title": g("title"),
            "published": g("published")[:10],
            "url": "https://arxiv.org/abs/" + (m.group(1) if m else ""),
        })
    return out


def arxiv_search(query, n):
    url = ARXIV + urllib.parse.urlencode({
        "search_query": query, "sortBy": "relevance",
        "sortOrder": "descending", "max_results": n})
    return arxiv_entries(fetch(url))


def arxiv_ids(ids):
    url = ARXIV + urllib.parse.urlencode({"id_list": ",".join(ids), "max_results": len(ids)})
    return arxiv_entries(fetch(url))


def crossref_query(title, n=3):
    url = CROSSREF + "?" + urllib.parse.urlencode({
        "query.bibliographic": title, "rows": n,
        "mailto": "how2how2how2-arch@users.noreply.github.com"})
    raw = fetch(url)
    if not raw:
        return []
    try:
        items = json.loads(raw)["message"]["items"]
    except Exception:
        return []
    out = []
    for it in items:
        t = (it.get("title") or [""])[0]
        out.append({
            "source": "crossref",
            "id": it.get("DOI", ""),
            "title": flat(t),
            "published": str((it.get("issued", {}).get("date-parts") or [[""]])[0][0]),
            "url": "https://doi.org/" + it.get("DOI", ""),
            "venue": flat((it.get("container-title") or [""])[0]),
        })
    return out


def crossref_doi(doi):
    raw = fetch(CROSSREF + "/" + urllib.parse.quote(doi))
    if not raw:
        return None
    try:
        it = json.loads(raw)["message"]
    except Exception:
        return None
    return {
        "source": "crossref",
        "id": it.get("DOI", ""),
        "title": flat((it.get("title") or [""])[0]),
        "published": str((it.get("issued", {}).get("date-parts") or [[""]])[0][0]),
        "url": "https://doi.org/" + it.get("DOI", ""),
        "venue": flat((it.get("container-title") or [""])[0]),
    }


# ---------------------------------------------------------------- harvest ---
# Queries derive from the study's actual field, not from a single system name.
QUERIES = [
    ("arxiv", 'all:"long-context language models" AND cat:cs.CL'),
    ("arxiv", 'all:"retrieval-augmented generation" AND cat:cs.CL'),
    ("arxiv", 'all:"retrieval augmented generation" AND all:"long context"'),
    ("arxiv", 'all:"dense retrieval" AND cat:cs.IR'),
    ("arxiv", 'all:"sparse retrieval" AND cat:cs.IR'),
    ("arxiv", 'all:"lost in the middle"'),
    ("arxiv", 'all:"position bias" AND all:"language model"'),
    ("arxiv", 'all:"needle in a haystack" AND all:"long context"'),
    ("arxiv", 'all:"context length" AND all:"evaluation" AND cat:cs.CL'),
    ("arxiv", 'all:"attention sink"'),
    ("arxiv", 'all:"KV cache" AND all:"compression"'),
    ("arxiv", 'all:"context degradation" AND all:"language model"'),
    ("arxiv", 'all:"distractor" AND all:"retrieval" AND all:"language model"'),
    ("arxiv", 'all:"irrelevant context" AND all:"reasoning"'),
    ("arxiv", 'all:"in-context learning" AND all:"distraction"'),
    ("arxiv", 'all:"multi-hop question answering" AND Aall:"retrieval"'.replace("Aall", "all")),
    ("arxiv", 'all:"citation" AND all:"attribution" AND all:"generation"'),
    ("arxiv", 'all:"memory" AND all:"LLM agents"'),
    ("arxiv", 'all:"sentence embeddings" AND all:"semantic textual similarity"'),
    ("arxiv", 'all:"transformer" AND all:"attention is all you need"'),
    ("arxiv", 'all:"BERT" AND all:"pre-training"'),
    ("arxiv", 'all:"BM25"'),
    ("arxiv", 'all:"chunking" AND all:"retrieval" AND cat:cs.IR'),
    ("arxiv", 'all:"reranking" AND all:"retrieval"'),
    ("arxiv", 'all:"long context" AND all:"benchmark"'),
    ("arxiv", 'all:"context window" AND all:"scaling"'),
    ("arxiv", 'all:"speculative decoding"'),
    ("arxiv", 'all:"prompt compression"'),
    ("arxiv", 'all:"RAG" AND all:"evaluation" AND cat:cs.CL'),
    ("arxiv", 'all:"agentic retrieval"'),
    ("arxiv", 'all:"tool use" AND all:"language model" AND cat:cs.CL'),
    ("arxiv", 'all:"information retrieval" AND all:"neural" AND cat:cs.IR'),
    ("arxiv", 'all:"question answering" AND all:"open domain"'),
    ("arxiv", 'all:"context" AND all:"hallucination"'),
    ("arxiv", 'all:"small language model"'),
    ("arxiv", 'all:"reading comprehension" AND all:"long document"'),
]

CROSSREF_TITLES = [
    "Okapi at TREC-3 BM25",
    "The probabilistic relevance framework BM25 and beyond",
    "BLEU a method for automatic evaluation of machine translation",
    "SQuAD 100000 questions for machine comprehension of text",
    "Natural Questions a benchmark for question answering research",
    "Attention is all you need",
    "BERT pre-training of deep bidirectional transformers for language understanding",
    "Language models are few-shot learners",
    "Sentence-BERT sentence embeddings using siamese BERT-networks",
    "Passage retrieval dense retrieval",
    "Retrieval-augmented generation for knowledge-intensive NLP tasks",
    "Dense passage retrieval for open-domain question answering",
    "BEIR a heterogeneous benchmark for zero-shot evaluation of information retrieval models",
    "MTEB massive text embedding benchmark",
    "Cognitive load theory and instructional design",
    "Human information processing capacity limits attention",
]


def harvest():
    cands = []
    print("arXiv term searches")
    for kind, q in QUERIES:
        print("  %s" % q[:70])
        got = arxiv_search(q, 8)
        for g in got:
            g["query"] = q
        cands += got
        time.sleep(SLEEP_ARXIV)
    print("Crossref bibliographic searches")
    for t in CROSSREF_TITLES:
        print("  %s" % t[:70])
        got = crossref_query(t, 2)
        for g in got:
            g["query"] = "crossref:" + t
        cands += got
        time.sleep(SLEEP_CROSSREF)
    # de-duplicate by (source, id)
    seen, uniq = set(), []
    for c in cands:
        k = (c["source"], c["id"])
        if not c["id"] or k in seen:
            continue
        seen.add(k)
        uniq.append(c)
    json.dump({"candidates": uniq}, open(CAND, "w", encoding="utf-8"), indent=1, sort_keys=True)
    print("candidates: %d -> %s" % (len(uniq), CAND))


# ----------------------------------------------------------------- verify ---
def verify():
    sel = json.load(open(SEL, encoding="utf-8"))["entries"]
    records, problems = [], []
    for e in sel:
        src, ident = e["source"], e["id"]
        if src == "crossref":
            rec = crossref_doi(ident)
            time.sleep(SLEEP_CROSSREF)
        else:
            got = arxiv_ids([ident])
            rec = got[0] if got else None
            time.sleep(SLEEP_ARXIV)
        status = "UNVERIFIED"
        if rec:
            a, b = norm(rec["title"]), norm(e["title"])
            if a == b:
                status = "exact"
            elif b in a or a in b:
                status = "substring"
            else:
                status = "MISMATCH"
        else:
            rec = {"title": "", "url": "", "published": ""}
        if status in ("UNVERIFIED", "MISMATCH"):
            problems.append((e["key"], status, e["title"], rec.get("title", "")))
        records.append({
            "key": e["key"],
            "title": rec.get("title") or e["title"],
            "recorded_title": e["title"],
            "source": src,
            "id": ident,
            "url": rec.get("url") or e["url"],
            "published": rec.get("published", ""),
            "status": status,
            "venue": rec.get("venue", ""),
            "difference": e["difference"],
        })
    json.dump({"entries": records, "problems": problems},
              open(OUT, "w", encoding="utf-8"), indent=1, sort_keys=True)
    ok = sum(1 for r in records if r["status"] in ("exact", "substring"))
    print("verified %d/%d, entries=%d, problems=%d" % (ok, len(records), len(records), len(problems)))
    for p in problems:
        print("  PROBLEM %s %s | recorded=%s | resolved=%s" % p)
    if problems:
        sys.exit(1)


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "harvest":
        harvest()
    elif cmd == "verify":
        verify()
    else:
        print(__doc__)
