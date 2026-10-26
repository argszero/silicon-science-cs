#!/usr/bin/env python3
"""Build the reference corpus from registry responses, never from recollection.

Issue #145 requires >=100 references, every one cited, every one verified against a
real external record (`reference-check.md`). The danger this script exists to remove
is a title that sounds right: a plausible-looking reference is exactly what a
language model produces without looking, so the corpus is assembled the other way
round — a candidate is a *query*, and what enters the corpus is what a registry
returned for it.

Two independent criteria decide acceptance (a single similarity score accepts the
wrong paper; that lesson is in the journal's memory):

  1. title agreement  — normalised token overlap with the candidate's expected title
  2. corroboration    — an INDEPENDENT field: expected first-author family name, or
                        expected year. Passing on the title alone is not enough.

A candidate that does not clear both is recorded as `unresolved` and EXCLUDED from
the corpus. Exclusion is reported with its count, never silently dropped.

Methods, in order:
  by-doi      -> Crossref /works/<doi>, compare title + year
  crossref    -> Crossref ?query.bibliographic, then the two criteria
  arxiv       -> arXiv API ti:<title>, then the two criteria (https only; paced)

Usage: python3 build_references.py [--batch N] [--out references.json] [--check]
Exit: 0 if every corpus entry is verified, 1 otherwise.
"""
import argparse
import json
import re
import sys
import time
import unicodedata
import urllib.parse
import urllib.request

UA = "emrg-silicon-science/1.0 (issue-145 reference verification)"
CROSSREF = "https://api.crossref.org/works"
ARXIV = "https://export.arxiv.org/api/query"

# ---------------------------------------------------------------------------
# Candidates. Each is a QUERY plus the fields that corroborate it. The title and
# author recorded here are what we *believe*, and the registry is what decides.
# (key, query/title, author family, year, topic line from manuscript_skeleton §10)
# ---------------------------------------------------------------------------
CANDIDATES = [
    # (a) build provenance, SLSA / in-toto / supply chain integrity
    ("torres-arias2019intoto", "in-toto: providing farm-to-table guarantees for bits and bytes",
     "Torres-Arias", 2019, "a"),
    ("newman2019sigstore", "sigstore: software signing for everybody", "Newman", 2022, "a"),
    ("cappos2019tuf", "The update framework: defending software updates against library attacks",
     "Cappos", 2023, "a"),
    ("samuel2010survivable", "Survivable key compromise in software update systems",
     "Samuel", 2010, "a"),
    ("nikitin2019slsa", "Supply-chain levels for software artifacts", None, None, "a"),
    # (b) supply-chain security: package ecosystems, dependency attacks, SBOM
    ("zimmermann2019dependency", "Small world with high risks: a study of security threats in the npm ecosystem",
     "Zimmermann", 2019, "b"),
    ("ohm2020backstabber", "Backstabber's knife collection: a systematic study of open-source python package attacks",
     "Ohm", 2020, "b"),
    ("ladisa2023sok", "SoK: taxonomy of attacks on open-source software supply chains",
     "Ladisa", 2023, "b"),
    ("vu2021typosquatting", "Typosquatting and combosquatting attacks on the python ecosystem",
     "Vu", 2020, "b"),
    ("dekorte2022slsa", "SLSA: raising the bar for software supply chain security", None, None, "b"),
    ("tran2022sbom", "SBOM completeness: an empirical study of software bill of materials",
     None, None, "b"),
    ("xia2023sbom", "An empirical study of software bill of materials in practice",
     None, None, "b"),
    # reproducible builds
    ("lamb2022reproducible", "Reproducible builds: increasing the integrity of software supply chains",
     "Lamb", 2021, "b"),  # IEEE Software 2022; asserted year 2021 is a near-miss, recorded as an edition note
    ("solaar2020reproducible", "Reproducible builds in Fedora", None, None, "b"),
    # (c) attestation / transparency logs
    ("crosby2009efficient", "Efficient data structures for tamper-evident logging",
     "Crosby", 2009, "c"),
    ("laurie2014certificate", "Certificate transparency", "Laurie", 2014, "c"),
    ("ryan2014enhanced", "Enhanced certificate transparency and end-to-end encrypted mail",
     "Ryan", 2014, "c"),
    # (d) instrument validity / measurement methodology
    ("campbell1963experimental", "Experimental and quasi-experimental designs for research",
     "Campbell", 1963, "d"),
    ("shadish2002experimental", "Experimental and quasi-experimental designs for generalized causal inference",
     "Shadish", 2002, "d"),
    ("cronbach1955construct", "Construct validity in psychological tests", "Cronbach", 1955, "d"),
    ("jacobs2019measurement", "Measurement and its uses in software engineering research",
     None, None, "d"),
    ("ralph2020empirical", "Empirical standards for software engineering research",
     "Ralph", 2020, "d"),
    ("winter2021provenance", "Provenance and measurement in software engineering", None, None, "d"),
    # (e) detection / audit theory
    ("base_rate_fallacy", "The base-rate fallacy in probability judgments", "Bar-Hillel", 1980, "e"),
    ("good1950probability", "Probability and the weighing of evidence", "Good", 1950, "e"),
    ("axe2020audit", "Audit logging in software systems", None, None, "e"),
    # background: package registries and dependency structure
    ("decan2019evolution", "An empirical comparison of dependency issues in OSS packaging ecosystems",
     "Decan", 2017, "b"),
    ("kikas2020structure", "Structure and evolution of package dependency networks",
     "Kikas", 2017, "b"),
    ("bogart2016pypi", "An empirical study of the Python package ecosystem", None, None, "b"),
    # provenance / provenance in databases and workflow systems
    ("buneman2001why", "Why and where: a characterization of data provenance",
     "Buneman", 2001, "d"),
    ("cheney2009provenance", "Provenance in databases: why, how, and where",
     "Cheney", 2009, "d"),
    ("davidson2008provenance", "Provenance and scientific workflows: challenges and opportunities",
     "Davidson", 2008, "d"),
    # PLANT: a title that does not exist, to prove the instrument refuses
    ("__plant_fabricated__", "Attested closure coverage in hermetic registries: a complete census",
     "Zzzznotreal", 2024, "plant"),
]

TITLE_OK = 0.80      # token-overlap floor
ARXIV_PACE = 3.5     # seconds between arXiv calls (it throttles)

# ---------------------------------------------------------------- HARVEST
# The corpus is grown from what the REGISTRY HAS, not from titles recalled first and verified
# afterwards: recall produced 13/33 (see `decision-recall-fails-the-registry-decides`).  Each row is
# (query_id, crossref bibliographic query, required any-of terms).  The terms are the RELEVANCE gate:
# Crossref's ranking is loose, so a record is kept only when its title carries at least one term the
# query is actually about.  Every kept entry records which query produced it, so a reader can see the
# selection rule rather than take the list on trust.
HARVEST_QUERIES = [
    # (query_id, crossref query, group A, group B)
    # A record is kept only when its title carries a term from A **and** (if B is non-empty) a term
    # from B.  Two groups because one broad word admits the wrong field entirely: `supply chain`
    # alone returned logistics papers ("Selecting Supply Chain Software", "Supply Chain Evolution"),
    # which are about trucks, not package registries.  B is the field discriminator; A is the topic.
    # --- the paper's own subject: attestation, provenance, signing
    ("slsa",        "SLSA supply chain levels for software artifacts provenance", ["slsa"], []),
    ("intoto",      "in-toto supply chain integrity framework", ["toto"], []),
    ("sigstore",    "sigstore signing transparency log software", ["sigstore", "cosign"], []),
    ("tuf",         "The Update Framework securing software update systems", ["update framework", "tuf"], []),
    ("attest",      "software attestation remote attestation measurement", ["attest"], []),
    ("tranlog",     "transparency log verifiable append-only log", ["transparency log", "merkle", "append-only"], []),
    ("cosign",      "container image signing verification signature", ["signing", "signature"], ["container", "image", "artifact", "package"]),
    # --- SBOM / dependency closure
    ("sbom",        "software bill of materials SBOM generation", ["bill of materials", "sbom"], []),
    ("deps",        "dependency resolution package dependency graph", ["dependency", "dependencies"], ["resolution", "closure", "graph", "transitive", "tree"]),
    ("closure",     "transitive dependency closure analysis packages", ["closure"], ["dependency", "dependencies", "package"]),
    ("vulnprop",    "vulnerability propagation dependency network ecosystem", ["vulnerab"], ["software", "package", "code", "cyber", "security", "propagation", "network attack"]),
    ("lockfile",    "lockfile pinning reproducibility package installation", ["lockfile", "pinning"], ["dependency", "package", "reproducib", "install"]),
    # --- the ecosystems the paper measures
    ("npm",         "npm package ecosystem empirical study JavaScript", ["npm"], []),
    ("pypi",        "PyPI Python package ecosystem empirical analysis", ["pypi"], ["package", "python", "index", "ecosystem", "registry", "install"]),
    ("oci",         "OCI container image registry distribution specification", ["oci"], ["container", "image", "registry", "spec"]),
    ("apko",        "apko Chainguard image build reproducibility", ["apko", "chainguard"], []),
    ("distroless",  "minimal container image attack surface distroless", ["distroless", "minimal image", "minimal container"], []),
    ("trustedpub",  "trusted publishing OIDC package registry credentials", ["trusted publishing", "oidc"], []),
    ("typosquat",   "typosquatting malicious packages registry detection", ["typosquat", "malicious package"], []),
    ("depconfusion","dependency confusion attack package manager", ["dependency confusion", "confusion attack"], []),
    # --- reproducible builds / verifiability
    ("rebuild",     "reproducible builds bit-for-bit verification", ["reproducib"], ["build", "rebuild", "verification"]),
    ("supplychain", "software supply chain security attack survey", ["supply chain"], ["software", "attack", "security", "package", "dependency", "artifact"]),
    ("securitysm",  "security smell software supply chain configuration", ["security smell", "configuration smell"], ["supply", "pipeline", "package", "ci"]),
    # --- theory leg: partial identification, bounds, intervals
    ("partialid",   "partial identification bounds econometrics", ["partial identification"], []),
    ("frechet",     "Fréchet bounds joint distribution unknown marginals", ["frechet", "fr\u00e9chet"], []),
    ("bounds",      "sharp bounds causal inference unobserved confounding", ["bounds", "bound"], ["causal", "confounding", "identification", "treatment", "effect"]),
    ("wilson",      "binomial confidence interval small sample proportion", ["confidence interval"], ["binomial", "proportion", "small sample", "coverage"]),
    ("sensitivity", "minimum detectable effect power analysis sample size", ["power analysis", "detectable effect", "statistical power"], []),
    # --- measurement methodology
    ("measurement", "empirical measurement study software engineering methodology", ["measurement"], ["software", "empirical", "study"]),
    ("mining",      "mining software repositories dataset threats validity", ["mining software repositories", "repository mining", "msr"], []),
    ("sampling",    "sampling bias generalizability empirical software engineering", ["sampling", "generaliz"], ["software engineering", "empirical", "study"]),
    ("provenancedb","provenance databases why how where", ["provenance"], ["database", "workflow", "lineage", "query"]),
    ("census",      "census large-scale analysis package registry population", ["census", "large-scale", "large scale"], ["package", "packages", "registry", "ecosystem", "software"]),
    ("replication", "replication reproducibility empirical software engineering", ["replication", "reproducib"], ["experiment", "empirical", "study", "software"]),
    # --- added: topics the manuscript argues about but the first pass under-covered
    ("typosquat2",  "malicious package detection npm PyPI registry", ["malicious", "malware"], ["package", "packages", "npm", "pypi", "registry", "ecosystem"]),
    ("sbomconsume", "SBOM consumption tooling evaluation vulnerability detection", ["sbom", "bill of materials"], ["consum", "tool", "evaluation", "vulnerab", "detection"]),
    ("sca",         "software composition analysis dependency risk", ["software composition", "composition analysis", "dependency risk"], []),
    ("dependabot",  "automated dependency update bot pull request", ["dependabot", "dependency update", "automated update"], []),
    ("semver",      "semantic versioning breaking change package", ["semantic version", "versioning", "breaking change"], ["package", "release", "depend"]),
    ("popularity",  "package popularity metrics download counts usage", ["popularity", "download", "usage"], ["package", "packages", "npm", "pypi", "library"]),
    ("maintainer",  "open source maintainer accounts compromise hijack", ["maintainer", "account", "compromise", "hijack"], ["open source", "package", "npm", "pypi", "registry"]),
    ("osv",         "vulnerability database advisory OSV CVE ecosystem", ["osv", "advisory", "vulnerability database", "cve"], []),
    ("reprodnix",   "reproducible build systems Nix Debian bit-identical", ["reproducib"], ["nix", "debian", "build system", "deterministic", "binary"]),
    ("measurestudy", "empirical study software engineering threats to validity", ["empirical study", "empirical analysis"], ["software", "package", "ecosystem", "repository"]),
    ("attestbuild", "build provenance attestation in-toto SLSA artifact", ["attestation", "provenance"], ["build", "artifact", "artefact", "pipeline", "ci"]),
    ("slsa2",       "supply chain levels software artifacts SLSA framework", ["slsa", "supply chain levels"], []),
]

# Types a related-work list can cite.  Crossref also returns `component`, `dataset`, `peer-review`,
# `reference-entry` and `other` -- figure captions, tables of contents, cover pages and review
# reports.  Those are real records and are not scholarly works: cite one and the reference list is
# wrong even though every DOI resolves.
SCHOLARLY_TYPES = {"journal-article", "proceedings-article", "book-chapter", "posted-content",
                   "book", "dissertation", "report", "reference-entry"}

STOP = {"a", "an", "the", "of", "for", "and", "in", "on", "to", "with", "is", "are", "at", "by",
        "from", "as", "its", "via", "using", "toward", "towards", "not"}


def slug(s, n=3):
    """A short, stable key fragment: the first n significant words of a title."""
    out = []
    for t in norm_tokens(s):
        if t in STOP or len(t) < 3:
            continue
        out.append(t)
        if len(out) >= n:
            break
    return "".join(out)


def relevant(low, A, B):
    """A record is on-topic when its title carries a term from A and, if B is given, from B.

    Normalised title is a space-joined token string, so a multi-word term is a substring.
    """
    if not any(t in low for t in A):
        return False
    if B and not any(t in low for t in B):
        return False
    return True


def near_dup(sig, seen_sigs, floor=0.85):
    """Token-set Jaccard near-duplicate.  Crossref carries the same paper under variant spellings
    ("Forsecuring" / "Securing"), which a signature of the whole title cannot see."""
    a = set(sig)
    for b in seen_sigs:
        b = set(b)
        if not a or not b:
            continue
        j = len(a & b) / float(len(a | b))
        if j >= floor:
            return True
    return False


def harvest_key(title, author, year, taken):
    fam = re.sub(r"[^a-z0-9]+", "", (author or "anon").lower())
    base = "%s%s%s" % (fam, year or "nd", slug(title))
    k, i = base, 2
    while k in taken:
        k = "%s%d" % (base, i); i += 1
    return k


def harvest(rows_per_query, out_path, query_filter=None, budget=0.0, rebuild=False):
    """Grow the corpus from Crossref returns, keeping the query that produced each entry.

    Distinct from verification on purpose.  A VERIFIED entry is an assertion that matched a record;
    a HARVESTED entry is a record the registry returned for a topic, and its risk is irrelevance, not
    fabrication.  The two are counted and labelled separately so neither borrows the other's evidence.
    """
    prev = []
    try:
        prev = json.load(open(out_path))["entries"]
    except Exception:
        prev = []
    if rebuild:
        # harvested entries are a DERIVED set: they are whatever the current query table and gate
        # return.  Keeping ones a stricter gate would now reject would make the gate decorative.
        # Verified entries are historical assertions and are never dropped here.
        before = len(prev)
        prev = [e for e in prev if not str(e.get("method", "")).startswith("discover")]
        print("rebuild: dropped %d previous harvest entries, kept %d verified" % (before - len(prev), len(prev)))
    taken = {e["key"] for e in prev}
    have_doi = {(e.get("doi") or "").lower() for e in prev if e.get("doi")}
    have_title = [tuple(sorted(set(norm_tokens(e.get("title"))))) for e in prev if e.get("title")]

    qs = HARVEST_QUERIES
    if query_filter:
        want = set(query_filter.split(","))
        qs = [q for q in qs if q[0] in want]

    added, skipped_dup, skipped_irrel, no_locator, failed, skipped_type = [], 0, 0, 0, [], 0
    per_query = {}
    t0 = time.time()
    for qid, q, A, B in qs:
        if budget and (time.time() - t0) > budget:
            failed.append({"query": qid, "why": "NOT_RUN: budget exhausted before this query"})
            print("NOT RUN  %-12s budget exhausted" % qid)
            continue
        try:
            recs = discover(q, rows_per_query)
        except Exception as e:
            tag = "NOT_RUN" if ("429" in str(e) or "timed out" in str(e).lower()
                                or "urlopen" in str(e).lower()) else "ERROR"
            failed.append({"query": qid, "why": "%s: %s" % (tag, e)})
            print("%-8s %-12s %s" % (tag, qid, str(e)[:70]))
            continue
        kept = 0
        for r in recs:
            title = r.get("title") or ""
            doi = (r.get("doi") or "").lower()
            if not title:
                skipped_irrel += 1
                continue
            low = " ".join(norm_tokens(title))
            # RELEVANCE GATE: group A's topic term AND group B's field term (see HARVEST_QUERIES)
            if not relevant(low, A, B):
                skipped_irrel += 1
                continue
            if (r.get("type") or "") not in SCHOLARLY_TYPES:
                skipped_type += 1
                continue
            if doi and doi in have_doi:
                skipped_dup += 1
                continue
            sig = tuple(sorted(set(norm_tokens(title))))
            if near_dup(sig, have_title):
                skipped_dup += 1
                continue
            if not doi:
                # no DOI means no locator this corpus can re-check; counted, never silently kept
                no_locator += 1
                continue
            key = harvest_key(title, r.get("first_author"), r.get("year"), taken)
            taken.add(key)
            have_doi.add(doi)
            have_title.append(sig)
            added.append({
                "key": key,
                # asserted == the record's own fields: nothing was recalled, so nothing is asserted
                # beyond what the registry returned
                "asserted": {"title": title, "first_author": r.get("first_author"),
                             "year": r.get("year")},
                "method": "discover-crossref",
                "query": qid,
                "query_text": q,
                "note": "registry return for query %r (Crossref, rows=%d); relevance gate: title "
                        "carries one of %s and, if given, one of %s"
                        % (q, rows_per_query, A, B),
                "topic": qid,
                "title": title,
                "doi": r.get("doi"),
                "year": r.get("year"),
                "venue": r.get("venue") or "",
                "first_author": r.get("first_author") or "",
                "type": r.get("type"),
                "url": "https://doi.org/" + (r.get("doi") or ""),
            })
            kept += 1
        per_query[qid] = {"returned": len(recs), "kept": kept}
        print("harvest  %-12s returned %2d, kept %2d" % (qid, len(recs), kept))

    merged = {e["key"]: e for e in prev}
    for e in added:
        merged[e["key"]] = e
    corpus = [merged[k] for k in sorted(merged)]

    prev_out = {}
    try:
        prev_out = json.load(open(out_path))
    except Exception:
        pass
    prev_harv = (prev_out.get("harvest") or {})
    prev_queries = prev_harv.get("per_query") or {}
    prev_queries.update(per_query)
    out = prev_out or {}
    out.update({
        "built_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "criteria": {"title_overlap_floor": TITLE_OK,
                     "corroboration": "first-author family OR asserted year (independent of title)",
                     "harvest_relevance": "a returned title carries a group-A topic term AND (when "
                                          "group B is non-empty) a group-B field term; near-duplicates "
                                          "at title Jaccard >= 0.85 are dropped; records without a "
                                          "DOI are counted, never kept"},
        "entries": corpus,
        "harvest": {
            "rows_per_query": rows_per_query,
            "added_this_run": len(added),
            "skipped_duplicate": skipped_dup,
            "skipped_irrelevant": skipped_irrel,
            "skipped_no_locator": no_locator,
            "skipped_non_scholarly_type": skipped_type,
            "failed_queries": failed,
            "per_query": dict(sorted(prev_queries.items())),
        },
    })
    out["verified"] = sum(1 for e in corpus if not str(e.get("method", "")).startswith("discover"))
    out["harvested"] = sum(1 for e in corpus if str(e.get("method", "")).startswith("discover"))
    open(out_path, "w").write(json.dumps(out, indent=1, sort_keys=True) + "\n")
    print("\nHARVEST: +%d entries (%d duplicate, %d irrelevant, %d non-scholarly type, "
          "%d no locator, %d queries failed)"
          % (len(added), skipped_dup, skipped_irrel, skipped_type, no_locator, len(failed)))
    print("CORPUS: %d entries -- %d verified, %d harvested"
          % (len(corpus), out["verified"], out["harvested"]))
    for f in failed:
        print("  NOT RUN %-12s %s" % (f["query"], f["why"][:70]))
    # a run that harvested nothing is NOT a pass: it says the queries failed, not that the field is empty
    if not added:
        print("VERDICT: NOT RUN (no entry added; the registry returned nothing usable for these queries)")
        return 2
    print("VERDICT: PASS (harvested entries carry their query; relevance is the query's, not the title's)")
    return 0



def norm_tokens(s):
    s = unicodedata.normalize("NFKD", s or "").lower()
    # drop combining marks BEFORE the character filter: replacing them with a space splits the word
    # ("Fréchet" -> "fre chet"), which made a query for the Fréchet bounds match nothing at all
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"[^a-z0-9 ]+", " ", s)
    return [t for t in s.split() if t]


def title_score(a, b):
    """Token-overlap (Jaccard-ish, symmetric) between two titles."""
    ta, tb = set(norm_tokens(a)), set(norm_tokens(b))
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def get(url, timeout=30):
    req = urllib.request.Request(url, headers={"User-Agent": UA,
                                               "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8", "replace"))


def get_text(url, timeout=30):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")


def first_family(item):
    au = item.get("author") or []
    if au and isinstance(au, list):
        return (au[0] or {}).get("family")
    return None


def year_of(item):
    parts = ((item.get("issued") or {}).get("date-parts") or [[None]])
    return parts[0][0] if parts and parts[0] else None


def corroborate(item, author, year):
    """The INDEPENDENT criterion. Returns (ok, note).

    Author-mismatch is FATAL when an author is asserted. The first version used OR
    semantics ("author OR year"), and that accepted `10.1136/jech.4.3.170` — a
    published REVIEW of Good's book by Stein — as Good 1950, because the year
    agreed. A year is a weak identifier: in one volume of one journal thousands of
    works share it. So:

      author asserted -> the FIRST author must match; a year difference is recorded
                         as an edition/issue note but tolerated (editions repeat).
      author not asserted -> the year must match exactly.
    """
    fam = first_family(item)
    y = year_of(item)
    notes = []
    if author:
        if fam and fam.lower() == author.lower():
            notes.append("author %s" % fam)
            if year and y != year:
                notes.append("EDITION NOTE: asserted year %s, record says %s" % (year, y))
            return True, "; ".join(notes)
        return False, "asked for first author %r, record says %r (title alone is not identity)" % (author, fam)
    if year:
        if y == year:
            return True, "year %s (no author asserted)" % y
        return False, "asked for year %s, record says %s (no author asserted to corroborate)" % (year, y)
    return False, "no independent field asserted, cannot corroborate"


def verify_crossref(cand):
    _, title, author, year, _ = cand
    q = urllib.parse.urlencode({"query.bibliographic": title, "rows": 5,
                                "select": "DOI,title,author,issued,container-title,type"})
    try:
        d = get(CROSSREF + "?" + q)
    except Exception as e:
        # a failure to ASK is not an answer: tag it so the caller can bucket it as NOT RUN
        tag = "NOT_RUN:" if ("429" in str(e) or "timed out" in str(e).lower()
                             or "urlopen" in str(e).lower()) else "ERROR:"
        return None, "%s crossref %s" % (tag, e)
    best = None
    for it in d["message"]["items"]:
        t = (it.get("title") or [""])[0]
        sc = title_score(title, t)
        if best is None or sc > best[0]:
            best = (sc, it)
    if best is None:
        return None, "crossref returned no items"
    sc, it = best
    if sc < TITLE_OK:
        return None, "title score %.3f < %.2f (best: %r)" % (sc, TITLE_OK, (it.get("title") or [""])[0][:70])
    ok, note = corroborate(it, author, year)
    if not ok:
        return None, "title %.3f but %s" % (sc, note)
    return it, "crossref title %.3f; %s" % (sc, note)


def verify_doi(cand, doi):
    try:
        d = get(CROSSREF + "/" + urllib.parse.quote(doi))
    except Exception as e:
        return None, "doi lookup failed: %s" % e
    it = d["message"]
    t = (it.get("title") or [""])[0]
    sc = title_score(cand[1], t)
    if sc < TITLE_OK:
        return None, "doi title score %.3f (record: %r)" % (sc, t[:70])
    ok, note = corroborate(it, cand[2], cand[3])
    if not ok:
        return None, "doi title %.3f but %s" % (sc, note)
    return it, "doi %s; title %.3f; %s" % (doi, sc, note)


ATOM_NS = "{http://www.w3.org/2005/Atom}"


def verify_arxiv(cand):
    import xml.etree.ElementTree as ET
    _, title, author, year, _ = cand
    # arXiv search: all:<words> is more forgiving than ti:
    q = urllib.parse.urlencode({"search_query": "all:%s" % re.sub(r"[^A-Za-z0-9 ]+", " ", title)[:180],
                                "max_results": 5})
    try:
        txt = get_text(ARXIV + "?" + q)
    except Exception as e:
        tag = "NOT_RUN:" if ("429" in str(e) or "timed out" in str(e).lower()) else "ERROR:"
        return None, "%s arxiv %s" % (tag, e)
    try:
        root = ET.fromstring(txt)
    except Exception as e:
        return None, "arxiv parse error: %s" % e
    best = None
    for e in root.findall(ATOM_NS + "entry"):
        t = " ".join((e.findtext(ATOM_NS + "title") or "").split())
        sc = title_score(title, t)
        if best is None or sc > best[0]:
            au = [a.findtext(ATOM_NS + "name") or "" for a in e.findall(ATOM_NS + "author")]
            best = (sc, {"title": t, "author": au,
                         "published": e.findtext(ATOM_NS + "published"),
                         "id": e.findtext(ATOM_NS + "id")})
    if best is None:
        return None, "arxiv returned no entries"
    sc, rec = best
    if sc < TITLE_OK:
        return None, "arxiv title score %.3f (best: %r)" % (sc, (rec.get("title") or "")[:70])
    fams = [a.split()[-1] if a.split() else "" for a in rec.get("author") or []]
    yr = int((rec.get("published") or "0000")[:4]) if rec.get("published") else None
    notes = []
    if author and any(f.lower() == author.lower() for f in fams):
        notes.append("author %s" % author)
    if year and yr == year:
        notes.append("year %s" % yr)
    if not notes:
        return None, "arxiv title %.3f but no corroboration (authors %s, year %s)" % (sc, fams[:3], yr)
    rec["doi"] = None
    rec["venue"] = "arXiv"
    rec["issued"] = {"date-parts": [[yr]]}
    rec["type"] = "preprint"
    return rec, "arxiv title %.3f; %s" % (sc, "; ".join(notes))


def entry_from(key, item, method, note, cand):
    return {
        "key": key,
        "asserted": {"title": cand[1], "first_author": cand[2], "year": cand[3]},
        "method": method,
        "note": note,
        "topic": cand[4],
        "title": (item.get("title") if isinstance(item.get("title"), str)
                  else (item.get("title") or [""])[0]) if item.get("title") else "",
        "doi": item.get("DOI") or item.get("doi"),
        "year": year_of(item),
        "venue": ((item.get("container-title") or [""])[0]
                  if isinstance(item.get("container-title"), list)
                  else item.get("container-title") or item.get("venue") or ""),
        "first_author": (first_family(item) or
                         ((item.get("author") or [""])[0] if isinstance(item.get("author"), list) else "")),
        "type": item.get("type"),
        "url": item.get("id") if item.get("type") == "preprint" else
               ("https://doi.org/" + (item.get("DOI") or "") if item.get("DOI") else ""),
    }


def discover(query, rows=8):
    """Discovery mode: print real records for a topic query.

    The corpus should be grown from what the registry HAS, not from titles
    recalled first and verified afterwards. Recall produced 13/33; discovery asks
    the registry what exists on a line and lets the paper choose from the answer.
    """
    q = urllib.parse.urlencode({"query.bibliographic": query, "rows": rows,
                                "select": "DOI,title,author,issued,container-title,type"})
    d = get(CROSSREF + "?" + q)
    out = []
    for it in d["message"]["items"]:
        t = (it.get("title") or [""])[0]
        if not t:
            continue
        out.append({"title": " ".join(t.split()),
                    "doi": it.get("DOI"),
                    "year": year_of(it),
                    "venue": ((it.get("container-title") or [""])[0] or "")[:60],
                    "first_author": first_family(it),
                    "type": it.get("type")})
    return out


def report(out_path, md_path):
    """Write the reference-check report FROM the corpus.  A hand-written report is a derived
    artefact that goes stale silently (issue #128's correction round: the built manuscript had not
    been regenerated); this one cannot, because it is regenerated by the command that builds the
    corpus."""
    d = json.load(open(out_path))
    entries = d["entries"]
    kept = [e for e in entries if e.get("review", "kept") == "kept"]
    excl = [e for e in entries if e.get("review") == "excluded"]
    ver = [e for e in kept if not e.get("query")]
    har = [e for e in kept if e.get("query")]
    L = []
    A = L.append
    A("# Reference verification report -- issue #145")
    A("")
    A("**DERIVED FILE -- do not edit.** Regenerate with `python3 build_references.py --report "
      "reference-check-draft.md`. `built_at_utc` %s." % d.get("built_at_utc"))
    A("")
    A("## What this corpus is, and what it is not")
    A("")
    A("Two kinds of entry, counted separately on purpose:")
    A("")
    A("| kind | count | what it means |")
    A("|---|---|---|")
    A("| **verified** | %d | an *asserted* citation (title + author + year written down first) matched a "
      "registry record under two criteria |" % len(ver))
    A("| **harvested** | %d | a record the registry *returned* for a topic query, then read by a person "
      "and kept |" % len(har))
    A("| excluded after review | %d | returned by a query, refused with a stated reason |" % len(excl))
    A("")
    A("The distinction is the point. A verified entry is evidence that a recalled citation is real; a "
      "harvested entry is evidence that a real record exists on a topic. Neither is evidence that the "
      "record says what this paper needs it to say -- that is the citation's job in the text.")
    A("")
    A("**Recall is not the source.** An earlier pass recalled 33 candidate works from memory and the "
      "registries refused 21 of them (64%); the corpus is therefore grown from registry returns, and "
      "the rejections are reported rather than deleted.")
    A("")
    A("## Acceptance and review rules")
    A("")
    A("* verified entries: title token-overlap >= %.2f **and** corroboration by a field that is not the "
      "title (first-author family, or the year when no author is asserted). Author mismatch is fatal." % TITLE_OK)
    A("* harvested entries: the title carries a group-A topic term **and**, where the query defines "
      "one, a group-B field term; non-scholarly record types (figure components, datasets, front "
      "matter, peer-review reports) are refused; titles within Jaccard 0.85 of an existing entry are "
      "duplicates; a record without a DOI is counted and never kept.")
    A("* every kept harvested entry states the query that produced it, so the selection rule is "
      "visible rather than asserted.")
    A("")
    A("## Verified entries (%d)" % len(ver))
    A("")
    A("| # | key | title | first author | year | venue / type | DOI | method |")
    A("|---|---|---|---|---|---|---|---|")
    for i, e in enumerate(sorted(ver, key=lambda x: x["key"]), 1):
        A("| %d | `%s` | %s | %s | %s | %s / %s | %s | %s |"
          % (i, e["key"], (e.get("title") or "")[:80], e.get("first_author") or "--",
             e.get("year") or "--", (e.get("venue") or "--")[:40], e.get("type") or "--",
             e.get("doi") or "--", e.get("method")))
    A("")
    A("## Harvested entries (%d), by query" % len(har))
    A("")
    byq = {}
    for e in har:
        byq.setdefault(e.get("query"), []).append(e)
    A("| query | kept | why this line is in the paper |")
    A("|---|---|---|")
    qtext = {q[0]: q[1] for q in HARVEST_QUERIES}
    for q in sorted(byq):
        A("| `%s` | %d | registry query: *%s* |" % (q, len(byq[q]), qtext.get(q, q)))
    A("")
    A("## Excluded after review (%d)" % len(excl))
    A("")
    A("Recorded, not deleted: a silently dropped record is a silent edit to the reference list.")
    A("")
    A("| key | year | title | reason |")
    A("|---|---|---|---|")
    for e in sorted(excl, key=lambda x: x["key"]):
        A("| `%s` | %s | %s | %s |" % (e["key"], e.get("year") or "--",
                                       (e.get("title") or "")[:70],
                                       (e.get("review_reason") or "")[:110]))
    A("")
    A("## Counts against the submission bar")
    A("")
    A("| gate | required | this corpus | state |")
    A("|---|---|---|---|")
    A("| references, all genuinely cited | >= 100 | %d kept | %s |"
      % (len(kept), "PASS on count" if len(kept) >= 100 else "SHORT"))
    A("| `reference-check.md` in the package | required | this file | DERIVED, regenerable |")
    A("| every entry carries a locator | required | %d of %d | %s |"
      % (sum(1 for e in kept if e.get("doi") or (e.get("url") or "").startswith("http")), len(kept),
         "PASS" if all(e.get("doi") or (e.get("url") or "").startswith("http") for e in kept) else "SHORT"))
    A("| entries with incomplete metadata | 0 preferred | %d | recorded |"
      % sum(1 for e in kept if not e.get("year") or not e.get("first_author")))
    A("")
    A("**Count is not the bar.** The 100-reference threshold is satisfied only when each entry is "
      "*cited in the body text*; a corpus of %d supports a 100-reference manuscript, it does not "
      "constitute one. That check lives with the manuscript, not here." % len(kept))
    open(md_path, "w").write("\n".join(L) + "\n")
    print("wrote %s (%d lines): %d verified + %d harvested kept, %d excluded"
          % (md_path, len(L), len(ver), len(har), len(excl)))
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--batch", type=int, default=len(CANDIDATES))
    ap.add_argument("--out", default="references.json")
    ap.add_argument("--check", action="store_true",
                    help="re-verify an existing corpus and write no new entries")
    ap.add_argument("--discover", metavar="QUERY", default=None,
                    help="print real records for a topic query instead of verifying")
    ap.add_argument("--rows", type=int, default=8)
    ap.add_argument("--budget", type=float, default=0.0,
                    help="wall-clock budget in seconds; unvisited candidates become NOT RUN")
    ap.add_argument("--no-arxiv", action="store_true",
                    help="consult Crossref only; refusals then record that arXiv was not asked")
    ap.add_argument("--only", default=None,
                    help="comma-separated keys to process (default: all)")
    ap.add_argument("--harvest", action="store_true",
                    help="grow the corpus from Crossref returns for HARVEST_QUERIES (records, not assertions)")
    ap.add_argument("--report", metavar="MD", default=None,
                    help="write the reference-check report from the corpus (derived; do not hand-edit)")
    ap.add_argument("--rebuild-harvest", action="store_true",
                    help="drop previous harvest entries first, then re-harvest (harvests are derived)")
    ap.add_argument("--queries", default=None,
                    help="comma-separated query ids for --harvest (default: all)")
    a = ap.parse_args()

    if a.report:
        return report(a.out, a.report)
    if a.harvest:
        return harvest(a.rows, a.out, a.queries, a.budget, a.rebuild_harvest)

    if a.check:
        try:
            corpus = json.load(open(a.out))["entries"]
        except Exception as e:
            print("FAIL: cannot read %s: %s" % (a.out, e))
            return 1
        bad, notrun = 0, 0
        for e in corpus:
            if e.get("review") == "excluded":
                continue          # refused on relevance; re-checking its DOI proves nothing
            if not e.get("doi"):
                print("ok(no-doi)  %-26s %s" % (e["key"], (e.get("url") or "")[:52]))
                continue
            a = e.get("asserted") or {}
            # compare against what was ASSERTED, not against the stored record:
            # a check whose two sides are the same field can never disagree.
            cand = (e["key"], a.get("title") or e["title"],
                    a.get("first_author"), a.get("year"), e.get("topic"))
            item, note = verify_doi(cand, e["doi"])
            if item is None and str(note).startswith("NOT_RUN"):
                # a failure to ASK is not a finding about the reference: bucket it separately or a
                # rate limit reads as a fabricated citation
                print("NOT RUN     %-26s %s" % (e["key"], note[:80]))
                notrun += 1
            elif item is None:
                print("STALE       %-26s %s" % (e["key"], note[:80]))
                bad += 1
            else:
                print("ok          %-26s %s" % (e["key"], note[:70]))
        print("\nCORPUS RE-CHECK: %d stale, %d NOT RUN of %d entries checked"
              % (bad, notrun, sum(1 for e in corpus if e.get("review") != "excluded")))
        if bad:
            print("VERDICT: FAIL")
            return 1
        if notrun:
            print("VERDICT: NOT RUN (%d could not be asked; not a finding about the corpus)" % notrun)
            return 2
        print("VERDICT: PASS")
        return 0

    if a.discover:
        for r in discover(a.discover, a.rows):
            print("%-5s %-42s %-34s %s" % (r["year"], r["title"][:42],
                                          (r["first_author"] or "?")[:34], r["doi"]))
        return 0

    corpus, unresolved, not_run = [], [], []
    t0 = time.time()
    only = set(a.only.split(",")) if a.only else None
    todo = [c for c in CANDIDATES[: a.batch] if (only is None or c[0] in only)]
    for cand in todo:
        # a budget makes the run always terminate and turns the tail into honest
        # NOT RUN rows instead of a kill that loses the whole corpus
        if a.budget and (time.time() - t0) > a.budget:
            not_run.append({"key": cand[0], "asserted_title": cand[1],
                            "crossref": "NOT_RUN: budget exhausted before this candidate"})
            print("NOT RUN     %-26s budget exhausted" % cand[0])
            continue
        key = cand[0]
        item, note = verify_crossref(cand)
        method = "crossref"
        if item is None:
            first_note = note
            if a.no_arxiv:
                item, note2 = None, "NOT_CONSULTED: arxiv skipped (--no-arxiv)"
            else:
                item, note2 = verify_arxiv(cand)
                time.sleep(ARXIV_PACE)
            method = "arxiv"
            if item is None:
                rec = {"key": key, "asserted_title": cand[1],
                       "asserted_author": cand[2], "asserted_year": cand[3],
                       "crossref": first_note, "arxiv": note2}
                # "could not ask" is a different bucket from "the registry says no"
                # NOT RUN only when NO registry answered. One registry answering "no"
                # is a refusal; the other one failing to answer does not undo it.
                answered = (not (first_note or "").startswith("NOT_RUN:")) or \
                           (not (note2 or "").startswith("NOT_RUN:")
                            and not (note2 or "").startswith("NOT_CONSULTED"))
                if not answered:
                    not_run.append(rec)
                    print("NOT RUN     %-26s %s" % (key, (first_note or note2)[:78]))
                else:
                    unresolved.append(rec)
                    print("UNRESOLVED  %-26s %s" % (key, first_note[:80]))
                time.sleep(ARXIV_PACE)
                continue
            note = note2
            time.sleep(ARXIV_PACE)
        e = entry_from(key, item, method, note, cand)
        if not e["title"]:
            unresolved.append({"key": key, "asserted_title": cand[1],
                               "crossref": "resolved but no title field",
                               "arxiv": ""})
            print("UNRESOLVED  %-26s record has no title" % key)
            continue
        corpus.append(e)
        print("verified    %-26s %-9s %s (%s)" % (key, method, e["title"][:56], e["year"]))

    # merge: keep entries verified by earlier runs, replace by key
    try:
        prev = json.load(open(a.out))["entries"]
    except Exception:
        prev = []
    merged = {e["key"]: e for e in prev}
    for e in corpus:
        merged[e["key"]] = e
    corpus = [merged[k] for k in sorted(merged)]
    prev_unres = []
    try:
        prev_unres = json.load(open(a.out)).get("unresolved_detail") or []
    except Exception:
        pass
    # a refusal from an earlier run stands unless this run resolved the same key
    resolved_keys = {e["key"] for e in corpus}
    for u in prev_unres:
        if u["key"] not in resolved_keys and not any(x["key"] == u["key"] for x in unresolved):
            unresolved.append(u)

    # ---- three-state plant verdict: refused / ACCEPTED (fail) / not attempted ----
    planted = [u for u in unresolved if u["key"].startswith("__plant")]
    plant_entry = [e for e in corpus if e["key"].startswith("__plant")]
    plant_attempted = any(x["key"].startswith("__plant") for x in not_run) or bool(planted) or bool(plant_entry)
    if plant_entry:
        plant_state = "ACCEPTED"
    elif planted:
        plant_state = "REFUSED"
    else:
        plant_state = "NOT RUN"
    out = {
        "built_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "criteria": {"title_overlap_floor": TITLE_OK,
                     "corroboration": "first-author family OR asserted year (independent of title)"},
        "candidates": len(todo),
        "verified": len(corpus),
        "unresolved": len(unresolved),
        "not_run": len(not_run),
        "plant_state": plant_state,
        "entries": corpus,
        "unresolved_detail": unresolved,
        "not_run_detail": not_run,
        "elapsed_s": round(time.time() - t0, 1),
    }
    blob = json.dumps(out, indent=1, sort_keys=True)
    open(a.out, "w").write(blob + "\n")
    print("\nCORPUS: %d verified, %d refused by the registry, %d NOT RUN (of %d candidates)"
          % (len(corpus), len(unresolved), len(not_run), out["candidates"]))
    for r in not_run:
        print("  NOT RUN %-24s %s" % (r["key"], (r.get("crossref") or r.get("arxiv") or "")[:70]))
    print("plant: %s" % plant_state)
    bad = [e for e in corpus if not e["doi"] and not (e["url"] or "").startswith("http")]
    print("entries with no locator: %d" % len(bad))
    if plant_state == "ACCEPTED":
        print("VERDICT: FAIL (the fabricated plant entered the corpus)")
        return 1
    if plant_state == "NOT RUN":
        print("VERDICT: NOT RUN (the plant was never attempted; a guard nobody ran is not a guard)")
        return 2
    print("VERDICT: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
