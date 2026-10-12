#!/usr/bin/env python3
"""Issue #122 -- reference DISCOVERY over the arXiv API.

Discovery is NOT curation and NOT verification.  An arXiv search returns noise (an off-topic paper
sharing a word), and this file records only WHAT WAS FOUND, with the query that found it.

The sibling `refs_tool.py` is the verifier (re-fetch by identifier, compare titles); the sibling
`refs_curate.py` is the curator.  Only curation decides what is cited; only the verifier decides
whether a citation is real.

Usage:  /usr/bin/python3 refs_discover.py [--refresh]
Cache:  refs/arxiv_cache/<slug>.json   (a re-run does not re-hit the API)
Out:    refs/candidates.json
"""
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

NS = {"a": "http://www.w3.org/2005/Atom"}
CACHE = "refs/arxiv_cache"
OUT = "refs/candidates.json"
MAX_RESULTS = 40

# SHORT phrases only: the API matches a quoted phrase VERBATIM, so a long query returns zero and
# reads like a thin literature (measured on #116: 40 of 46 long queries returned 0 results).
QUERIES = [
    # --- the construct: the self-consuming loop and the failure it is named for ----------------
    ("model-collapse", "model collapse"),
    ("self-consuming", "self-consuming"),
    ("self-consuming-generative", "self-consuming generative"),
    ("recursive-training", "recursive training"),
    ("generative-collapse", "generative model collapse"),
    ("data-collapse", "data collapse"),
    ("training-on-synthetic", "training on synthetic data"),
    ("synthetic-data", "synthetic data"),
    ("synthetic-data-llm", "synthetic data LLM"),
    ("model-autophagy", "model autophagy"),
    # --- the protocol: how the pool is formed, which is the axis P2 turns on -------------------
    ("data-mixture", "data mixture"),
    ("data-mixing-law", "data mixing law"),
    ("data-curriculum", "data curriculum"),
    ("replay", "experience replay"),
    ("distillation", "knowledge distillation"),
    ("self-distillation", "self-distillation"),
    ("self-training", "self training"),
    ("self-play", "self-play"),
    ("data-selection", "data selection"),
    ("dataset-curation", "dataset curation"),
    ("deduplication", "deduplication"),
    ("data-quality-filter", "quality filtering"),
    # --- the theory: the exact chain this direction is built on --------------------------------
    ("branching-process", "branching process"),
    ("galton-watson", "Galton-Watson"),
    ("perron-frobenius", "Perron-Frobenius"),
    ("markov-stationary", "Markov chain stationary"),
    ("population-dynamics", "population dynamics"),
    ("mean-field", "mean field"),
    ("jensen-inequality", "Jensen inequality"),
    ("tail-bound", "tail bound"),
    ("rare-event", "rare event simulation"),
    ("coupon-collector", "coupon collector"),
    ("support-recovery", "support recovery"),
    ("empirical-measure", "empirical measure"),
    ("wasserstein", "Wasserstein distance"),
    ("kl-divergence", "Kullback-Leibler"),
    ("information-geometry", "information geometry"),
    ("fisher-rao", "Fisher-Rao"),
    # --- the measured phenomenon: what collapse looks like --------------------------------------
    ("mode-collapse", "mode collapse"),
    ("diversity-collapse", "diversity collapse"),
    ("entropy-collapse", "entropy collapse"),
    ("distribution-shift", "distribution shift"),
    ("covariate-shift", "covariate shift"),
    ("catastrophic-forgetting", "catastrophic forgetting"),
    ("continual-learning", "continual learning"),
    ("tail-forgetting", "forgetting rare"),
    ("generalization-bound", "generalization bound"),
    # --- the mitigation literature (what the field has actually done) ---------------------------
    ("data-augmentation", "data augmentation"),
    ("regularization-collapse", "regularization"),
    ("entropy-regularization", "entropy regularization"),
    ("early-stopping", "early stopping"),
    ("benchmark-contamination", "benchmark contamination"),
    ("data-contamination", "data contamination"),
    # =============================================================================================
    # SECOND PASS (R522) -- CONVERGING QUERIES.
    #
    # Why a second pass exists at all.  The curator ranks each family by QUERY SUPPORT (how many
    # discovery queries returned the entry).  Measured after the first pass: `construct` carried
    # 20 of its 24 entries at support >= 2 while EVERY other family sat at 1 (theory 14/14,
    # measurement 16/16).  The obvious reading -- "the other families are thin" -- is WRONG, and
    # the query sets themselves say why: the 10 `construct` queries are PARAPHRASES OF ONE OBJECT
    # ("model collapse", "generative model collapse", "data collapse", "recursive training",
    # "training on synthetic data", ...), so any central paper is hit by several of them; the 16
    # `theory` queries instead name SIXTEEN DISTINCT OBJECTS (coupon collector, Perron-Frobenius,
    # Jensen, Fisher-Rao, Wasserstein, ...), so a central paper is hit by exactly one.  Support is
    # therefore comparable across families only when each family's query set overlaps the same way
    # -- it is a property of the QUERY SET, not of the literature.
    #
    # So this block gives the enumerative families their own paraphrases: a SECOND, independently
    # WORDED query for the same object.  A paper central to the object is then found by both, and
    # support >= 2 means what it was always read as meaning.  The null is explicit and checkable --
    # if a paraphrase partner returns a DISJOINT set, the ranking is not stable and support is
    # noise, which is a finding rather than a failure.
    #
    # Sources are unchanged (no pre-print of this paper, no author's own work).
    # --- theory: a paraphrase partner for each named object above ---------------------------------
    ("coupon-collector-problem", "coupon collector problem"),
    ("branching-processes", "branching processes"),
    ("extinction-probability", "extinction probability"),
    ("galton-watson-process", "Galton-Watson process"),
    ("stationary-distributions", "stationary distributions"),
    ("hitting-times", "hitting times"),
    ("large-deviations", "large deviations"),
    ("multinomial-distribution", "multinomial distribution"),
    ("concentration-inequality", "concentration inequality"),
    ("jensen-s-inequality", "Jensen's inequality"),
    ("empirical-process", "empirical process"),
    ("optimal-transport", "optimal transport"),
    ("fisher-information", "Fisher information"),
    # --- measurement: a paraphrase partner for the contamination / shift instruments -------------
    ("contamination-detection", "contamination detection"),
    ("test-set-leakage", "test set leakage"),
    ("data-leakage", "data leakage"),
    ("benchmark-leakage", "benchmark leakage"),
    ("ood-detection", "out-of-distribution detection"),
    ("train-test-overlap", "train-test overlap"),
    # --- mechanism: a paraphrase partner for each way support is lost ----------------------------
    ("catastrophic-interference", "catastrophic interference"),
    ("diversity-loss", "diversity loss"),
    ("generator-collapse", "generator collapse"),
    ("posterior-collapse", "posterior collapse"),
    ("sample-diversity", "sample diversity"),
    ("long-tailed-recognition", "long-tailed recognition"),
    # --- protocol: a paraphrase partner for each pool-formation object ---------------------------
    ("data-mixing", "data mixing"),
    ("coreset-selection", "coreset selection"),
    ("sample-selection", "sample selection"),
    ("pseudo-labeling", "pseudo-labeling"),
    ("dataset-distillation", "dataset distillation"),
    ("generative-replay", "generative replay"),
    # --- prevention: a paraphrase partner for the mitigation objects -----------------------------
    ("collapse-mitigation", "collapse mitigation"),
    ("entropy-bonus", "entropy bonus"),
    ("distribution-matching", "distribution matching"),
    ("rehearsal", "rehearsal"),
    # --- adjacent: a paraphrase partner for the neighbouring loops -------------------------------
    ("class-incremental-learning", "class-incremental learning"),
    ("incremental-learning", "incremental learning"),
    ("test-time-adaptation", "test-time adaptation"),
    ("online-adaptation", "online adaptation"),
    ("self-improvement", "self improvement"),
    ("bootstrapping-generation", "bootstrapping generation"),
]


def slug(q):
    return re.sub(r"[^a-z0-9]+", "-", q.lower()).strip("-")


def fetch(query, refresh=False):
    os.makedirs(CACHE, exist_ok=True)
    path = os.path.join(CACHE, slug(query) + ".json")
    if os.path.exists(path) and not refresh:
        with open(path) as f:
            return json.load(f), True   # cache hit -- no request was made
    url = ("https://export.arxiv.org/api/query?search_query="
           + urllib.parse.quote('all:"%s"' % query)
           + "&sortBy=relevance&sortOrder=descending&max_results=%d" % MAX_RESULTS)
    raw = ""
    ok = False
    for attempt in range(4):
        try:
            with urllib.request.urlopen(url, timeout=45) as r:
                raw = r.read().decode("utf-8", "replace")
            ok = True
            break
        except Exception as e:
            if attempt == 3:
                print("  ! fetch failed: %s (%s)" % (query, e), file=sys.stderr)
            time.sleep(3 * (attempt + 1))
    ents = []
    parsed = False
    if raw:
        try:
            root = ET.fromstring(raw)
            parsed = True
            for e in root.findall("a:entry", NS):
                # keep the FULL identifier: pre-2007 ids carry a category prefix (math/0508451),
                # and stripping it to the bare number makes the id unresolvable (arXiv answers
                # HTTP 400) -- measured on #118's first verification run.
                rid = e.find("a:id", NS).text.replace("http://arxiv.org/abs/", "")
                tt = " ".join(e.find("a:title", NS).text.split())
                pub = e.find("a:published", NS).text[:10]
                cats = [c.get("term") for c in e.findall("a:category", NS)]
                ents.append(dict(id=rid, title=tt, published=pub, cats=cats))
        except ET.ParseError:
            print("  ! parse failed: %s" % query, file=sys.stderr)
    # A FAILED request must NOT be cached.  Writing the empty result of a throttled first call makes
    # a transient failure permanent AND indistinguishable from "the literature is empty" -- measured
    # here: the direction's own core query `all:"model collapse"` cached `[]` on the first attempt
    # while a direct retry returned entries.  Only a SUCCESSFUL request may write the cache, and a
    # successful empty result is recorded as such (with `ok`), so the two stay distinguishable.
    if not (ok and parsed):
        print("  ! not cached (request did not succeed): %s" % query, file=sys.stderr)
        return ents, False
    with open(path, "w") as f:
        json.dump(ents, f, indent=1)
    return ents, False


def main():
    refresh = "--refresh" in sys.argv
    cand = {}
    print("discovery over %d queries (MAX_RESULTS=%d)" % (len(QUERIES), MAX_RESULTS))
    # ENFORCE the short-phrase rule instead of only documenting it: the API matches the quoted
    # phrase VERBATIM, so a query of more than 3 words is very likely to return 0 and to read as a
    # thin literature.  Measured this round: all four 4-word queries returned exactly 0, while the
    # tool's own comment already said so -- a documented constraint that is not enforced gets
    # violated by the next reader, including me.
    long_q = [k for k, q in QUERIES if len(q.split()) > 3]
    if long_q:
        print("  ! queries longer than 3 words (likely empty, prefer a shorter phrase): %s"
              % ", ".join(long_q), file=sys.stderr)
    # ENFORCED, not documented: two DIFFERENT query strings that slug() to the SAME cache file
    # collide -- the second one silently reads the first one's cached entries, reports the same
    # ids, and the two look like independent queries that AGREE.  Convergence by construction is
    # exactly the failure this round's design must not have ("mean field" and "mean-field" are the
    # measured shape: identical slug, different API query).  A collision is a hard error, because
    # its effect is invisible downstream: support rises and nothing in the artefact says why.
    # (Written as an explicit loop, NOT a comprehension: the first version put the `setdefault`
    # that POPULATES the map inside the comprehension's expression, which is evaluated only when
    # the guard condition has already passed -- so the map stayed empty and the guard could never
    # fire.  A check whose state is updated only on the branch that needs it is a check that has
    # never run.  It was caught by planting a real collision and watching it pass.)
    seen_slug, collide = {}, []
    for k, q in QUERIES:
        s = slug(q)
        if s in seen_slug:
            collide.append((k, seen_slug[s], q))
        else:
            seen_slug[s] = k
    if collide:
        for k, first, q in collide:
            print("  ! CACHE-KEY COLLISION: '%s' and '%s' share slug '%s'" % (first, k, slug(q)),
                  file=sys.stderr)
        sys.exit("refusing to run: %d cache-key collision(s) would make support converge by "
                 "construction" % len(collide))
    empty = []
    for i, (key, q) in enumerate(QUERIES, 1):
        ents, cached = fetch(q, refresh)
        if not ents:
            empty.append(key)
        print("  [%2d/%d] %-26s -> %d" % (i, len(QUERIES), key, len(ents)))
        for e in ents:
            c = cand.setdefault(e["id"], dict(id=e["id"], title=e["title"], published=e["published"],
                                              cats=e["cats"], queries=[]))
            if key not in c["queries"]:
                c["queries"].append(key)
        # Politeness applies to REQUESTS: sleeping after a cache hit is a 3-second delay for a
        # request that was never made (measured: 94 cached queries cost ~5 min of pure sleep).
        if not cached:
            time.sleep(3)
    os.makedirs("refs", exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(dict(n_queries=len(QUERIES), n_candidates=len(cand), empty_queries=empty,
                       # the query TEXT of each key travels with the pool: the curator must be able
                       # to ask whether two queries that found the same entry are really two
                       # phrasings or one phrase nested inside the other, and a key cannot answer
                       # that (the keys are already slugged).
                       query_text=dict(QUERIES),
                       candidates=sorted(cand.values(), key=lambda x: x["id"])), f, indent=1)
    print("\n%d unique candidates -> %s" % (len(cand), OUT))
    if empty:
        print("queries that returned nothing (recorded, NOT silently dropped): %s" % ", ".join(empty))


if __name__ == "__main__":
    main()
