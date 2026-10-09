#!/usr/bin/env python3
"""Harvest candidate references from Crossref and arXiv by TOPIC.

Everything these APIs return is a REAL record, so a candidate list harvested this way cannot
contain a fabricated citation -- the selection problem becomes relevance, not existence.
Raw responses are cached under refs/raw/ so the harvest is re-runnable without the network.
"""
import json, os, sys, time, urllib.parse, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "raw")
os.makedirs(RAW, exist_ok=True)

CROSSREF_TOPICS = [
    "software specification brittleness", "specification maintenance formal methods",
    "mutation testing survey", "equivalent mutants mutation testing",
    "test oracle problem", "metamorphic testing", "property based testing",
    "invariant inference dynamic detection", "regression test selection",
    "flaky tests empirical study", "test brittleness maintenance",
    "co-evolution specification implementation", "formal methods industrial adoption survey",
    "proof maintenance interactive theorem prover", "proof engineering verification effort",
    "refinement calculus specification", "alloy lightweight formal methods",
    "tla+ specification verification", "design by contract", "runtime verification monitors",
    "automated program repair", "verified compilation translation validation",
    "differential testing compilers", "assertion checking software", "coverage criteria adequacy",
    "software evolution change impact analysis", "fault detection effectiveness test suite",
    "verification cost model formal proof", "model based testing", "contract inference",
]
ARXIV_TOPICS = [
    ("cs.PL", "specification maintenance"), ("cs.SE", "mutation testing"),
    ("cs.SE", "test oracle"), ("cs.SE", "property-based testing"),
    ("cs.SE", "flaky test"), ("cs.PL", "formal specification evolution"),
    ("cs.LO", "proof repair"), ("cs.SE", "metamorphic testing"),
    ("cs.PL", "type system brittleness"), ("cs.SE", "regression testing selection"),
    ("cs.PL", "refinement types"), ("cs.SE", "LLM test generation"),
    ("cs.PL", "program equivalence"), ("cs.SE", "reproducibility empirical study"),
    ("cs.LO", "proof assistant library evolution"),
]

def get(url, path):
    if os.path.exists(path):
        return json.load(open(path))
    req = urllib.request.Request(url, headers={"User-Agent": "issue-114-bibliography/1.0 (mailto:noreply@example.org)"})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=45) as r:
                data = json.loads(r.read().decode("utf-8", "replace"))
            json.dump(data, open(path, "w"))
            return data
        except Exception as exc:
            print(f"    retry {attempt+1}: {type(exc).__name__}: {exc}", file=sys.stderr)
            time.sleep(2)
    return None

out = {"crossref": {}, "arxiv": {}}
for i, t in enumerate(CROSSREF_TOPICS):
    q = urllib.parse.quote(t)
    url = (f"https://api.crossref.org/works?query.bibliographic={q}&rows=12"
           f"&select=DOI,title,author,issued,container-title,type,short-container-title")
    d = get(url, os.path.join(RAW, f"cr_{i:02d}.json"))
    out["crossref"][t] = len(d["message"]["items"]) if d else 0
    print(f"  crossref [{i:02d}] {t:<45} {out['crossref'][t]} items")
    time.sleep(0.4)

for i, (cat, term) in enumerate(ARXIV_TOPICS):
    q = urllib.parse.quote(f"cat:{cat} AND all:{term}")
    url = (f"https://export.arxiv.org/api/query?search_query={q}"
           f"&sortBy=submittedDate&sortOrder=descending&max_results=15")
    p = os.path.join(RAW, f"ax_{i:02d}.xml")
    if not os.path.exists(p):
        req = urllib.request.Request(url, headers={"User-Agent": "issue-114-bibliography/1.0"})
        try:
            with urllib.request.urlopen(req, timeout=45) as r:
                open(p, "wb").write(r.read())
        except Exception as exc:
            print(f"    arxiv fail: {type(exc).__name__}: {exc}", file=sys.stderr)
        time.sleep(3)
    n = open(p, "rb").read().count(b"<entry>") if os.path.exists(p) else 0
    out["arxiv"][f"{cat}/{term}"] = n
    print(f"  arxiv    [{i:02d}] {cat} {term:<32} {n} entries")

json.dump(out, open(os.path.join(HERE, "harvest_counts.json"), "w"), indent=1)
print("done")
