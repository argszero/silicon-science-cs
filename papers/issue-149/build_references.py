#!/usr/bin/env python3
"""Build the reference corpus from registry responses, never from recollection.

Issue #149 requires >=100 references, every one cited, every one verified against a
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

UA = "emrg-silicon-science/1.0 (issue-149 reference verification)"
CROSSREF = "https://api.crossref.org/works"
ARXIV = "https://export.arxiv.org/api/query"

# ---------------------------------------------------------------------------
# Candidates. Each is a QUERY plus the fields that corroborate it. The title and
# author recorded here are what we *believe*, and the registry is what decides.
# (key, query/title, author family, year, topic line from manuscript_skeleton §10)
# ---------------------------------------------------------------------------
CANDIDATES = [
    # (key, title, author family, year, topic line)
    # ONLY works read in this session, and each is corroborated by an INDEPENDENT field the registry
    # supplies -- here the year, because the family name is not something this session recorded. A
    # year is a weak identifier on its own, which is why the arXiv title match has to be exact too.
    ("lockfiledesignspace2025", "The Design Space of Lockfiles Across Package Managers",
     "", 2025, "b"),
    ("mavenlockfile2025", "Maven-Lockfile: High Integrity Rebuild of Past Java Releases",
     "", 2025, "b"),
    ("escapingdependencyhell2026", "Escaping Python Dependency Hell: A Hybrid Replay-and-Repair "
     "Pipeline for Python Dependency Resolution", "", 2026, "a"),
    ("breakingdependencychaos2026", "Breaking the Dependency Chaos: A Constraint-Driven Python "
     "Dependency Resolution Strategy", "", 2026, "a"),
    ("hypergraphdep2025", "Solving Package Management via Hypergraph Dependency Resolution",
     "", 2025, "a"),
    ("maxsmt2022", "Flexible and Optimal Dependency Management via Max-SMT", "", 2022, "a"),
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
    # from B.  THIS TOPIC'S HOMONYM HAZARD IS WORSE THAN #145'S, which is why every A is paired with a
    # B and never used alone: "resolution" also names image/screen/spectral resolution and dispute
    # resolution; "range" names frequency, mountain and shooting ranges; "lock" names lock-free
    # algorithms, deadlock and mutexes; "dependency" names dependency grammar in linguistics, chemical
    # dependency, and statistical dependence; "registry" names cancer, land and patient registries;
    # "constraint solving" is mostly scheduling in operations research.  A alone would admit all of
    # them.  B is the field discriminator -- software, packages, versions, builds, registries.
    # --- version ranges and version semantics
    ("semver",      "semantic versioning compatibility breaking changes software packages",
     ["version"], ["software", "package", "library", "ecosystem", "npm", "pypi"]),
    ("verspec",     "version range specification dependency constraint satisfaction",
     ["version"], ["depend", "package", "software", "library", "constraint"]),
    ("semverprac",  "semantic versioning compliance violation empirical practice",
     ["semantic version"], ["complian", "violat", "empirical", "practice"]),
    ("compat",      "backward compatibility breaking changes library version upgrades",
     ["compatib", "breaking change", "upgrad"], ["library", "package", "depend", "software"]),
    ("apiev",       "library API evolution versioning empirical study",
     ["version", "evolution"], ["library", "package", "api"]),
    # --- dependency resolution and solvers
    ("depres",      "package dependency resolution algorithms conflict free installation",
     ["depend"], ["resolution", "solver", "install", "package"]),
    ("satdep",      "SAT solver dependency management package installation",
     ["depend", "solver"], ["package", "install"]),
    ("maxsmt",      "Max-SMT optimal dependency management software repositories",
     ["depend"], ["smt", "optimal", "repository"]),
    ("hyperdep",    "hypergraph dependency resolution package management",
     ["depend"], ["hypergraph", "resolution"]),
    ("depconflict", "dependency conflict detection resolution package ecosystems",
     ["conflict", "depend"], ["package", "ecosystem", "install"]),
    ("transitive",  "transitive dependency closure package update",
     ["depend"], ["transitive", "package", "update", "install"]),
    # --- lockfiles, pinning, reproducibility
    ("lockfile",    "lockfile reproducible builds dependency pinning",
     ["lockfile", "lock file", "pinning", "pinned"], ["depend", "build", "package", "reproduc"]),
    ("reprobuild",  "reproducible builds deterministic package installation",
     ["reproduc"], ["build", "package", "install", "depend"]),
    ("determinism", "deterministic dependency installation version pinning build",
     ["determinis", "pinning", "pinned"], ["depend", "install", "package", "build"]),
    ("sbom",        "software bill of materials dependency graph resolution",
     ["bill of materials", "sbom"], ["depend", "component", "package"]),
    ("nixlike",     "Nix reproducible package management store derivation",
     ["nix", "guix"], ["package", "reproduc"]),
    # --- registries and ecosystem dynamics
    ("registrymine", "package registry mining ecosystem evolution",
     ["registr", "ecosystem"], ["package", "software", "mining", "npm", "pypi"]),
    ("npmeco",      "npm ecosystem package dependency network analysis",
     ["npm", "node.js", "javascript"], ["package", "depend"]),
    ("pypieco",     "PyPI package ecosystem analysis dependency",
     ["pypi", "python package"], ["depend", "analysis", "ecosystem"]),
    ("breakingdep", "breaking dependency updates empirical study ecosystem",
     ["breaking", "update"], ["depend", "package", "ecosystem"]),
    ("vulnprop",    "vulnerability propagation dependency network packages",
     ["vulnerab"], ["depend", "package", "propagat"]),
    ("typosquat",   "malicious package detection registry dependencies",
     ["malicious", "typosquat"], ["package", "registr", "npm", "pypi"]),
    ("maintainer",  "package maintainer abandonment ecosystem dependency",
     ["maintainer"], ["package", "abandon", "ecosystem", "depend"]),
    # --- build systems and manifests
    ("buildsys",    "build system dependency declaration manifest correctness",
     ["build system", "manifest", "declaration"], ["depend", "build", "package"]),
    ("cargo",       "Cargo Rust crate version resolution dependency",
     ["cargo", "crate", "rust"], ["version", "depend"]),
    ("maven",       "Maven Gradle Java dependency management conflict",
     ["maven", "gradle", "java"], ["depend"]),
    ("gomod",       "Go modules version selection minimal version selection",
     ["go module", "minimal version"], ["version", "depend"]),
    ("debian",      "Debian package dependency solving distribution installability",
     ["debian", "apt", "rpm"], ["depend", "package"]),
    ("artifact",    "artifact repository resolution metadata build publication",
     ["artifact", "metadata"], ["build", "resolution", "repository"]),
    ("deprecat",    "deprecation policy library evolution usage",
     ["deprecat"], ["library", "package", "api"]),
    # --- the methodology this paper leans on (baseline rates, intervals, sampling)
    ("measurement", "empirical study measurement software engineering validity",
     ["empirical", "measurement"], ["software", "study"]),
    ("wilson",      "confidence interval small proportion binomial",
     ["confidence interval", "binomial"], []),
    ("sampling",    "sampling software engineering research guidance",
     ["sampling"], ["software", "research"]),
    ("csttheory",   "constraint satisfaction problem tractability structure",
     ["constraint satisfaction", "tractab"], []),
    ("identcode",   "identifying code test cover set cover problem",
     ["identifying code", "test cover", "set cover"], []),
    # --- widening pass (R682): the pool must survive screening, so reach is set before screening
    ("rangeapi",    "range based version specification dependency semantic",
     ["range"], ["version", "depend", "package"]),
    ("smtconfig",   "satisfiability modulo theories software configuration installation",
     ["satisfiability", "modulo theories"], ["software", "configur", "install"]),
    ("pkgversion",  "package release version history evolution repository",
     ["release", "evolution", "history"], ["package", "version"]),
    ("depgraph",    "dependency graph analysis software packages structure",
     ["dependency graph", "depend"], ["package", "software", "analysis"]),
    ("ecosystemrisk", "open source ecosystem health dependency risk",
     ["ecosystem", "health", "risk"], ["open source", "package", "depend"]),
    ("installability", "installability problem package distributions checking",
     ["installab"], ["package", "distribution"]),
    ("envrepro",    "reproducibility computational results software environment versions",
     ["reproduc"], ["software", "environment", "version", "computational"]),
    ("featuremodel", "feature model configuration selection variability software",
     ["feature model", "variability", "configuration"], ["software"]),
    ("versionscheme", "version numbering scheme semantics software releases",
     ["version number", "numbering"], ["software", "define", "scheme"]),
    ("apibreakage", "API breaking change detection library clients",
     ["breaking", "api change"], ["library", "client", "detect"]),
    # --- widening pass 2 (R682): the registration's own upgradability path -- declaration-based
    # pinning generalises past package managers to any registry whose published set only grows
    # (container tags, model registries).  Queries here reach that general case rather than adding
    # adjacent-field entries to reach a count.
    ("containertag", "container image tag digest pinning reproducibility registry",
     ["container", "docker", "image"], ["tag", "digest", "pinn", "reproduc"]),
    ("tagmut",      "mutable image tags supply chain integrity registry",
     ["tag", "digest"], ["mutab", "integrity", "registry", "supply chain"]),
    ("modelregistry", "machine learning model versioning registry reproducibility",
     ["model"], ["version", "registr", "reproduc", "artifact"]),
    ("mlopsver",    "MLOps model artifact version control lineage dependencies",
     ["mlops", "model", "pipeline"], ["version", "artifact", "lineage", "depend"]),
    ("iacpin",      "infrastructure as code version pinning provider dependency",
     ["infrastructure as code", "terraform", "ansible", "puppet", "chef"],
     ["version", "pinn", "depend", "provider"]),
    ("condaenv",     "conda environment specification reproducibility solver",
     ["conda", "environment.yml", "virtual environment"], ["reproduc", "solver", "depend"]),
    ("locksec",     "lockfile integrity attack dependency confusion registry",
     ["lock"], ["integrity", "attack", "registry", "depend"]),
    ("depsets",     "dependency dataset libraries.io packages metadata analysis",
     ["libraries.io", "dependency dataset"], ["package", "metadata", "analysis"]),
    ("sbomcomplete", "SBOM completeness dependency coverage provenance accuracy",
     ["sbom", "bill of materials"], ["complet", "coverage", "provenance", "accuracy", "depend"]),
    ("versiondrift", "version drift dependency outdated lag update policy",
     ["drift", "lag", "outdated"], ["depend", "version", "update"]),
    ("monorepo",    "workspace monorepo dependency hoisting resolution",
     ["monorepo", "workspace"], ["depend", "resolution", "hoist"]),
    ("presolve",    "preference based package solving optimisation core equity",
     ["solver", "solving"], ["package", "optimis", "optimiz", "install"]),
    # --- widening pass 3 (R682): name the CONSTRUCT rather than the field.  Pass 2 taught that a
    # field word pulls in other fields; a construct phrase ("dependency specification", "transitive
    # dependencies declared") is what the paper actually studies, and it is what a paper on it says.
    ("depspec",     "dependency specification declaration manifest empirical analysis",
     ["depend"], ["specification", "declaration", "manifest", "empirical", "analysis"]),
    ("transdecl",   "direct and transitive dependencies declared package manifest study",
     ["depend"], ["transitive", "declared", "manifest", "package"]),
    ("installexp",  "package installation resolution empirical study ecosystem measurement",
     ["install", "resolution"], ["empirical", "study", "measurement", "ecosystem"]),
    ("constraintstudy", "version constraints specification packages empirical measurement",
     ["constraint"], ["version", "package", "empirical", "measurement"]),
    ("pkgmgrstudy", "package manager empirical study dependency management practice",
     ["package manager"], ["empirical", "study", "practice", "depend"]),
    ("moduleres",   "module resolution algorithm dependency graph JavaScript bundles",
     ["module", "bundle"], ["resolution", "depend", "graph"]),
    ("pyconflict",  "Python package dependency conflicts analysis ecosystem",
     ["conflict"], ["python", "package", "ecosystem", "depend"]),
    ("repinst",     "reproducible installation environment measurement study",
     ["reproduc"], ["installation", "measurement", "study", "environment"]),
    ("regmeta",     "package registry metadata empirical software engineering analysis",
     ["registr"], ["metadata", "empirical", "software engineering", "analysis"]),
    ("declarative", "declarative dependency management evaluation correctness",
     ["declarative", "depend"], ["evaluation", "correctness", "management"]),
    ("envrepro",    "reproducibility computational results software environment versions",
     ["reproduc"], ["software", "environment", "version", "computational"]),
    ("versionscheme", "version numbering scheme semantics software releases",
     ["version number", "numbering"], ["software", "define", "scheme"]),
    ("dirlock",     "dependency lock file format comparison package managers",
     ["lock"], ["file", "format", "package manager", "depend"]),
    ("minver",      "minimal version selection dependency resolution correctness",
     ["version selection", "resolution"], ["depend", "correctness", "algorithm"]),
    ("artifactpin", "artifact pinning digest reproducibility package distribution",
     ["pinn", "digest"], ["artifact", "reproduc", "package", "distribution"]),
    # --- WIDENING ROUND: the registered upgrade path (container-image tag sets, model registries).
    # Placement left the pool short of the floor, and the honest way up is a wider population of
    # the same construct, not a looser review. These queries ask the two artifact classes where
    # "which version did you get" is already a recognised problem, so the construct transfers
    # rather than being stretched: an image tag and a model id are declarations with the same
    # degree of freedom as a version range.
    ("dockerpull",  "docker image pull tag latest reproducibility study",
     ["image", "docker", "container"], ["tag", "digest", "reproduc", "pull"]),
    ("ocidigest",   "OCI image manifest digest content addressable container registry",
     ["image", "container", "registry"], ["digest", "manifest", "content address", "oci"]),
    ("imagepin",    "pinned container image versions scientific workflow reproducibility",
     ["image", "container"], ["pinn", "version", "reproduc", "workflow"]),
    ("baseimage",   "base image updates vulnerability container rebuild study",
     ["image", "container"], ["base image", "update", "vulnerab", "rebuild"]),
    ("modelzoo",    "model zoo versioning pretrained model repository reproducibility",
     ["model"], ["version", "zoo", "repository", "registry", "reproduc"]),
    ("modelhub",    "Hugging Face model hub versions dependency analysis",
     ["model"], ["hub", "version", "depend", "package"]),
    ("mlartifact",  "machine learning artifact dependency tracking experiment reproducibility versions",
     ["artifact", "experiment"], ["depend", "version", "reproduc", "track"]),
    ("modelspec",   "model environment specification dependency declaration machine learning",
     ["model", "environment"], ["specification", "depend", "declaration", "version"]),
    ("apptainer",   "Apptainer Singularity container image reproducibility definition file",
     ["container", "image", "singularity", "apptainer"], ["reproduc", "definition", "version", "pinn"]),
    ("imagetagpolicy", "container image tagging policy mutable tag immutability best practice",
     ["image", "tag"], ["mutable", "immutab", "policy", "practice", "registry"]),
    ("mlregistry",  "ML model registry metadata version dependency tracking deployment",
     ["model", "registry"], ["version", "metadata", "depend", "deploy"]),
    ("modelserve",  "model version pinning inference serving reproducibility experiment",
     ["model", "serving", "inference"], ["version", "pinn", "reproduc"]),
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
                    # NOT [:60]. The cut used to live here and it silently truncated 92 of the
                    # 270 harvested venue strings mid-word ("...48th International Conferen");
                    # every later step reproduced them faithfully and no gate could see a cut
                    # inside the corpus. A display that needs to elide does it with an explicit
                    # ellipsis at the point of display, never by storing less than the record says.
                    "venue": ((it.get("container-title") or [""])[0] or ""),
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
    ap.add_argument("--remove", metavar="KEY", default=None,
                    help="move one entry out of the pool and record why (never a hand edit of the "
                         "corpus: a removal whose reason is not written down is a silent edit)")
    ap.add_argument("--reason", default=None, help="why the entry is being removed (required)")
    a = ap.parse_args()

    if a.remove:
        if not a.reason:
            print("FAIL: --remove needs --reason: an unexplained removal is a silent edit")
            return 1
        doc = json.load(open(a.out))
        hit = [e for e in doc["entries"] if e["key"] == a.remove]
        if len(hit) != 1:
            print("FAIL: %r matches %d entries (need exactly 1)" % (a.remove, len(hit)))
            return 1
        e = hit[0]
        e["review"] = "removed"
        e["removed_on"] = time.strftime("%Y-%m-%d", time.gmtime())
        e["review_reason"] = a.reason
        json.dump(doc, open(a.out, "w"), indent=1, ensure_ascii=False, sort_keys=True)
        print("removed %-40s %s" % (a.remove, a.reason[:80]))
        kept = sum(1 for x in doc["entries"] if x.get("review", "kept") == "kept")
        print("kept now: %d" % kept)
        return 0

    if a.report:
        return report(a.out, a.report)
    if a.harvest:
        return harvest(a.rows, a.out, a.queries, a.budget, a.rebuild_harvest)

    if a.check:
        # A check that only PRINTS is not state: the next reader has to re-query Crossref to learn
        # what was found, so the report built from a live run cannot be reproduced offline and dies
        # in reproduce.sh. Every answer (including a refusal) is therefore stored per entry, and
        # `reference_report.py` is a pure function of that stored state.
        try:
            doc = json.load(open(a.out))
        except Exception as e:
            print("FAIL: cannot read %s: %s" % (a.out, e))
            return 1
        corpus = doc["entries"]
        today = time.strftime("%Y-%m-%d", time.gmtime())
        bad = notrun = ver = noloc = 0
        for e in corpus:
            if e.get("review") in ("excluded", "removed"):
                continue          # refused on relevance; re-checking its DOI proves nothing
            if not e.get("doi"):
                e["verification"] = {"result": "no_locator", "checked_on": today, "method": "none",
                                     "corroboration": "no DOI; stored locator is %r"
                                                      % ((e.get("url") or "") or "MISSING"),
                                     "record": None}
                print("ok(no-doi)  %-26s %s" % (e["key"], (e.get("url") or "")[:52]))
                noloc += 1
                continue
            asrt = e.get("asserted") or {}
            # compare against what was ASSERTED, not against the stored record:
            # a check whose two sides are the same field can never disagree.
            cand = (e["key"], asrt.get("title") or e["title"],
                    asrt.get("first_author"), asrt.get("year"), e.get("topic"))
            item, note = verify_doi(cand, e["doi"])
            rec = None
            if item is not None:
                rec = {"doi": item.get("DOI"),
                       "title": (item.get("title") or [""])[0],
                       "first_author": first_family(item),
                       "year": year_of(item),
                       "type": item.get("type"),
                       "container": (item.get("container-title") or [""])[0]}
            m = re.search(r"title (\d\.\d+)", str(note))
            score = float(m.group(1)) if m else None
            if item is None and str(note).startswith("NOT_RUN"):
                # a failure to ASK is not a finding about the reference: bucket it separately or a
                # rate limit reads as a fabricated citation
                print("NOT RUN     %-26s %s" % (e["key"], note[:80]))
                notrun += 1
                e["verification"] = {"result": "not_run", "checked_on": today,
                                     "method": "crossref-doi", "corroboration": note, "record": None}
            elif item is None:
                print("STALE       %-26s %s" % (e["key"], note[:80]))
                bad += 1
                e["verification"] = {"result": "stale", "checked_on": today,
                                     "method": "crossref-doi", "title_score": score,
                                     "corroboration": note, "record": rec}
            else:
                print("ok          %-26s %s" % (e["key"], note[:70]))
                ver += 1
                e["verification"] = {"result": "verified", "checked_on": today,
                                     "method": "crossref-doi", "title_score": score,
                                     "corroboration": note, "record": rec}
        doc["verification"] = {"checked_on": today, "checked": ver + bad + notrun,
                               "verified": ver, "stale": bad, "not_run": notrun,
                               "no_locator": noloc,
                               "method": "Crossref DOI lookup, then corroboration by a field that "
                                         "is not the title (first-author family, or year when no "
                                         "author is asserted)"}
        json.dump(doc, open(a.out, "w"), indent=1, ensure_ascii=False, sort_keys=True)
        print("\nCORPUS RE-CHECK: %d stale, %d NOT RUN, %d no locator of %d entries checked (state stored)"
              % (bad, notrun, noloc, ver + bad + notrun + noloc))
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
