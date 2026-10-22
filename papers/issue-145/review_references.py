#!/usr/bin/env python3
"""review_references.py -- the HUMAN pass over the harvested corpus, recorded.

Why this file exists.  `build_references.py --harvest` grows the corpus from what Crossref returns,
and Crossref's relevance ranking is loose in ways no term list fixes: it returns figure captions,
conference front matter, book reviews, and — the expensive ones — records that share a word with the
topic and belong to another field entirely (`pyPI` = Tropical Cyclone *Potential Intensity*;
"Vulnerability and the Moral Nature of Dependency Relations"; "OSV" = *OSPF* vulnerability checking;
"attestation" in art philosophy).  A term gate cannot separate those, and pretending it does would be
worse than reporting it.

So the corpus has TWO states and this script is the boundary between them:

  * mechanical (the query + term gate + scholarly-type filter) -- cheap, reproducible, and blind to
    same-word-different-field;
  * reviewed (this file) -- a person read the title and said whether the record belongs in this paper.

Every rejection is recorded WITH ITS REASON, because a silently dropped record is a silent edit to
the reference list.  Rejections do not delete the entry: it stays in references.json marked
`excluded`, so the reader sees what was considered and refused, not only what survived.

Usage: python3 review_references.py [--show]
"""
import io, json, re, sys, collections

OUT = "references.json"

# Whole queries whose yield is not used.  A query can pass the term gate and still return a line the
# paper does not argue with; naming the query is more honest than rejecting its entries one by one.
QUERY_REJECTS = {
    "osv": "CVE/NVD vulnerability-database records: adjacent to the paper, not argued with. Citing "
           "them would be padding, and padding is what a 100-reference bar invites.",
    "census": "the query's surviving yield is epidemiological ('micro census', census of population); "
              "the term 'census' names a demographic instrument, not a registry census",
    "sca": "matched the OTHER sense of 'software composition' (component-based design, access "
           "control), not software composition analysis of dependencies",
}

# Individual records: key -> reason.  Grouped by the kind of mistake, so the list is a lesson list.
KEY_REJECTS = {}

_FRAGMENT = "not a standalone work: a caption/front-matter/chapter fragment Crossref indexes as a record"
_MEDICAL = "different field: the title shares a word with the topic and is a medical/biological study"
_PHILOSOPHY = "different field: 'attestation'/'provenance' in philosophy or art history, not in builds"
_OTHER_FIELD = "different field: shares a term with the topic, is about something else"
_LOWQ = "same author, same year, six generic titles: a self-published series, not a body of related work"
_THIN = "thin/unverifiable venue or a software package rather than a work of research"
_FUTURE = "year is in the future (2027): the record's issued date cannot be right"

for k in ("anon1983dependencygraph", "anon2007firstinternationalsymposium*",
          "anon2007fourthinternationalwor",
          "anon2012confidenceintervalssim", "anon2017remoteattestation",
          "anonndprovenancescientificdata"):
    KEY_REJECTS[k] = _FRAGMENT

for k, why in {
    "anon2024examiningsoftwarebill": "SBOM in *logistics* supply chains (shipping), not software",
    "anonndapplyingdigitalsignature": "signature applied to printed output, not software artifacts",
    "bikel2008eventmatchingtransiti": "transitive closure of dependency *relations* in event matching, "
                                      "not package dependency closure",
    "kumar2026riskcutaneousmelanoma": _MEDICAL,
    "kumar2026riskhaematologicmalig": _MEDICAL,
    "mahpour2016pymappythonpackage": _MEDICAL,
    "bright2020irradpypythonpackage": _OTHER_FIELD + " (atmospheric science package)",
    "takefuji2021pythonprogrammingp": _MEDICAL,
    "khan2006velocityimagemodel": _OTHER_FIELD + " (signature = handwritten-signature verification)",
    "parmar2020imageprocessingbased": _OTHER_FIELD + " (signature duplication in images)",
    "tiwari2024unveilinggraphstruct": _OTHER_FIELD + " (microservice call graphs)",
    "pagourtzis2001pvmcomputationtr": _OTHER_FIELD + " (parallel-computing transitive closure)",
    "hyderjr2026drivenfailureanalys": _OTHER_FIELD + " (LSTM failure prediction in engineering systems)",
    "laeuchli2023softwarebasedremot": _OTHER_FIELD + " (quantum-entanglement attestation)",
    "zahid2025integrationintelsgx": "hardware-enclave attestation; retained nowhere the paper argues "
                                    "— the build-attestation lineage is cited through its own papers",
    "radanliev2023generativepretrai": _OTHER_FIELD + " (GPT/NLP article, SBOM named only in passing)",
    "shukla2025enhancingcybersecuri": _THIN,
    "kumar2025securitycyberphysical": "additive-manufacturing (physical) supply chain",
    "ts2026detectionreportingtyposq": "typosquatting of *domains*, not of package names",
    "coene2021discoverwebpacknpm": _THIN,
    "yan2027mvrfdetmaliciouspackage": _FUTURE,
    "kasemsuwan2017osvospfvulnerabi": _OTHER_FIELD + " (OSV here = OSPF routing vulnerability)",
    "wang2008designsurvivabilityqua": _OTHER_FIELD + " (quantum survivability database)",
    "pantalony2019presenceprovenanc": _PHILOSOPHY,
    "pederson2016pasteurquadrantpro": _PHILOSOPHY,
    "werapun2026windchainphysicscon": _OTHER_FIELD + " (blockchain attestation of wind resources)",
    "bottomley2005compromiserouteop": _THIN,
    "cock2025thoughtsgenerativecont": _THIN,
    "havinganddesignsoftwarecomposi": "matched the other sense of 'software composition' (component "
                                      "design), not dependency composition analysis",
    "parrendndcomponentbasedaccess": "component-based access control, not dependency composition",
    "walkerden1999empiricalstudyana": _OTHER_FIELD + " (effort estimation)",
    "anon2025drivensbomautomated": _THIN,
    # found by `--check`, not by the read-through: the record carries neither an author nor a year,
    # so the two-criterion rule cannot corroborate it at all.  An entry nobody can corroborate is
    # unverifiable, and an unverifiable citation is refused rather than kept with a caveat.
    "anonndpartialidentificationecono": "unverifiable: the registry record carries no author and no "
                                        "year, so no field independent of the title can corroborate it",
}.items():
    KEY_REJECTS[k] = why

# the six same-author supply-chain items, and the CRAN package records
for k in ("syed2024casestudiessoftware", "syed2024devsecopsintegrationsu",
          "syed2024emergingtrendssoftware", "syed2024implementingcomprehens",
          "syed2024keytechnologiessupply", "syed2024supplychainsoftware"):
    KEY_REJECTS[k] = _LOWQ


# ---------------------------------------------------------------- SECOND PASS
# The first pass above excluded what was SALIENT -- logistics supply chains, medical cohorts, art
# philosophy: things whose titles obviously belong to another field.  It missed the harder class:
# records that share the paper's WORD and name an adjacent-but-different CONSTRUCT.  A second pass,
# organised by the paper's own construct and asking of each group "does this name a mechanism, a
# population or a method this paper uses?", found 17 more.
#
# The lesson is about the procedure, not the attention: a relevance review that scans a list for
# what looks wrong is a salience filter.  A relevance review that walks the paper's claims and asks
# what each claim needs cited is a criterion filter, and only the second one converges.
SECOND_PASS = {}

# (1) "attestation" is two different constructs.  These are hardware / remote attestation: a machine
# measuring its own runtime state to a challenger (TPM, SGX, DAA).  Build provenance names an
# artifact's inputs.  Not one of them names an input, so citing the group would pad the list with a
# word match.  Ten of the eleven are excluded; ONE stays, cited once in §2 as the construct this
# paper is not, so a reader coming from the security community finds the distinction made rather
# than the question left open.
for k in ("ammar2021delegatedattestation", "anon2011remoteattestation",
          "chen2010directanonymousattestation", "cui2009credibilityattestationproperty",
          "li2008propertybasedremote", "preibsch2025siteattestationbrowser",
          "qin2009componentpropertybased", "wagner2022heterogeneousremoteattestation",
          "xu2011efficientremoteattestation", "zhang2014virtualmachineanonymous"):
    SECOND_PASS[k] = ("wrong construct: hardware/remote attestation (a machine attesting its runtime "
                      "state), not build provenance (an artifact naming its inputs). One representative "
                      "is cited in §2 to draw the contrast; the other ten would be a word match.")

# (2) "signature" is three different constructs.  These two verify HANDWRITTEN signatures from
# scanned images -- offline signature verification is a document-forensics task.  The `cosign` query
# returned the wrong sense of the word entirely.
for k in ("gillmanindersingh2012statisticalfeaturesbased",
          "hadjadj2024texturalfeaturesencrypted"):
    SECOND_PASS[k] = ("wrong construct: offline/handwritten signature verification (document "
                      "forensics), not code or artifact signing")

# (3) the canonical false friend this package's own tests name, still in the kept set: pyPI here is
# the Tropical Cyclone Potential Intensity package, published in a geoscientific modelling journal.
SECOND_PASS["gilford2020pypitropicalcyclone"] = (
    "wrong construct: 'pyPI' is the Tropical Cyclone Potential Intensity package (DOI prefix "
    "10.5194 = Geoscientific Model Development), not the Python Package Index")

# (4) "dependency" is three constructs.  Parsing dependencies between WORDS, and requirement
# dependency graphs between SPECIFICATION items, are not package dependency closures.
for k in ("bohnetbernd2013graphbasedtransition", "samosir2019generatingrequirementdependency",
          "exman2019softwaremodularitycoupling"):
    SECOND_PASS[k] = ("wrong construct: 'dependency' in the dependency-parsing / requirements / "
                      "coupling sense, not a package dependency closure")

# (5) the same work twice: two SSRN preprints of one paper, the 2025 one a revision of the 2024 one.
# Counting both would inflate the total by one and cite one work as two.
SECOND_PASS["tamanna2024unravelingchallengessupply"] = (
    "duplicate work: the 2024 SSRN preprint (10.2139/ssrn.4979511) is superseded by the 2025 "
    "revision (ssrn.5119626) already in the corpus; citing both counts one work twice")

# (6) record quality: the registry's own title field is truncated mid-sentence ("ML) in Software
# Vulnerability Management..."), so the entry cannot be cited as a work even though the topic fits.
SECOND_PASS["radanliev2023softwarevulnerabilitymanageme"] = (
    "record quality: the registry title is truncated mid-sentence ('ML) in Software Vulnerability "
    "Management...'), so the entry cannot be cited as a bibliographic object")


def resolve(named, corpus_keys):
    """Map a named key to the corpus key it means, by exact match then by UNIQUE prefix.

    Keys above were first transcribed from a listing that truncated them at 30 characters, so an
    exact-match-only lookup silently dropped 28 intended rejections and the "reviewed" corpus kept
    work the review had refused.  A prefix that is ambiguous is not resolved: guessing which of two
    entries was meant is how a review becomes decoration.
    """
    out, absent, ambiguous = {}, [], []
    for k in named:
        if k.endswith("*"):
            # explicit "every entry under this prefix" -- the four front-matter records of one
            # proceedings share a prefix and ALL of them are refused; say so instead of picking one
            hits = [c for c in sorted(corpus_keys) if c.startswith(k[:-1])]
            if hits:
                for h in hits:
                    out[h] = k
            else:
                absent.append(k)
            continue
        if k in corpus_keys:
            out[k] = k
            continue
        hits = [c for c in corpus_keys if c.startswith(k)]
        if len(hits) == 1:
            out[k] = hits[0]
        elif hits:
            ambiguous.append((k, hits))
        else:
            absent.append(k)
    return out, absent, ambiguous


def main():
    show = "--show" in sys.argv
    d = json.load(io.open(OUT, encoding="utf-8"))
    entries = d["entries"]
    corpus_keys = {e["key"] for e in entries}
    resolved, absent, ambiguous = resolve(KEY_REJECTS, corpus_keys)
    if ambiguous:
        print("FAIL ambiguous key(s) -- say which entry is meant:")
        for k, hits in ambiguous:
            print("  %-30s -> %s" % (k, hits))
        return 1
    rejects = {}
    for k, why in KEY_REJECTS.items():
        if k.endswith("*"):
            for ck, src in resolved.items():
                if src == k:
                    rejects[ck] = why
        elif k in resolved:
            rejects[resolved[k]] = why

    by_query = collections.Counter()
    for e in entries:
        e.pop("review", None)
        e.pop("review_reason", None)
        q = e.get("query")
        ck = "verified" if not q else q
        if q in QUERY_REJECTS:
            e["review"], e["review_reason"] = "excluded", QUERY_REJECTS[q]
        elif e["key"] in rejects:
            e["review"], e["review_reason"] = "excluded", rejects[e["key"]]
        elif e["key"] in SECOND_PASS:
            e["review"], e["review_reason"] = "excluded", SECOND_PASS[e["key"]]
        elif re.search(r"^CRAN:", e.get("venue") or "") or re.match(r"^(LPower|pwrss|rdpower)\b",
                                                                   e.get("title") or ""):
            e["review"], e["review_reason"] = "excluded", _THIN + " (a software package, not a paper)"
        else:
            e["review"], e["review_reason"] = "kept", ""
        by_query[(ck, e["review"])] += 1

    kept = [e for e in entries if e["review"] == "kept"]
    excl = [e for e in entries if e["review"] == "excluded"]
    d["review"] = {
        # NO wall clock: a timestamp inside the reviewed corpus makes the corpus, and everything
        # derived from it, different on every run. git records when; the file records what.
        "method": "two passes, both recorded with a reason, entries kept in the file marked "
                  "'excluded' so the exclusions are auditable: (1) salience -- a title obviously in "
                  "another field; (2) criterion -- organised by the paper's own construct, asking of "
                  "each group whether it names a mechanism, population or method the paper uses. "
                  "The second pass found 17 the first missed, all sharing the paper's word and "
                  "naming an adjacent construct",
        "kept": len(kept), "excluded": len(excl),
        "reasons": dict(collections.Counter(e["review_reason"] for e in excl).most_common()),
    }
    json.dump(d, open(OUT, "w"), indent=1, sort_keys=True)
    open(OUT, "a").write("\n")

    n2 = sum(1 for e in excl if e["key"] in SECOND_PASS)
    print("CORPUS %d entries -> %d kept, %d excluded (%d on the second pass)"
          % (len(entries), len(kept), len(excl), n2))
    ver = sum(1 for e in kept if not e.get("query"))
    print("  kept: %d verified (an asserted citation that matched a record), %d harvested"
          % (ver, len(kept) - ver))
    print("  rejected for record quality, by reason:")
    for r, n in collections.Counter(e["review_reason"] for e in excl).most_common():
        print("    %2d  %s" % (n, r[:96]))
    print("  named rejections: %d resolved to a corpus entry, %d named a record the type filter "
          "already dropped" % (len(resolved), len(absent)))
    for k in absent:
        print("    (absent) %s" % k)
    if show:
        for e in excl:
            print("  X %-30s %s" % (e["key"][:30], e["review_reason"][:60]))
    # a review that keeps everything has not reviewed anything
    if not excl:
        print("VERDICT: FAIL (nothing was excluded; the pass did not happen)")
        return 1
    print("VERDICT: PASS (%d kept, %d excluded with a stated reason)" % (len(kept), len(excl)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
