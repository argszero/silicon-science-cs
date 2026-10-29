#!/usr/bin/env python3
"""review_references.py -- issue #149: the two-pass review of the harvested corpus, recorded.

WHY THIS FILE EXISTS.  `build_references.py --harvest` grows the corpus from what Crossref returns for
a topic query, and a relevance gate over the TITLE cannot separate a homonym from the topic.  This
topic's homonyms are worse than the sibling paper's, because five of its core words name major
constructs in other fields:

    pinning      -> domain-wall pinning in ferromagnets, pinning in control theory
    SMT          -> statistical machine translation, not satisfiability modulo theories
    dependency   -> dependency grammar (linguistics), chemical dependency, statistical dependence
    ecosystem    -> public health, entrepreneurship, distributed acoustic sensing
    resolution   -> image / spectral / dispute resolution
    registry     -> cancer, land, patient registries
    manifest     -> psychology inventories ("Manifest Anxiety"), political declarations

So the corpus has TWO states and this file is the boundary between them:

  * mechanical  -- query + term gate + scholarly-type filter: cheap, reproducible, and blind to
                   same-word-different-field;
  * reviewed    -- a person read the title and said whether the record belongs in this paper.

TWO PASSES, because one pass has two different jobs and merging them hides both:
  PASS 1 (salience)  -- the title is obviously about something else (a medical, physical, linguistic or
                        archival construct that merely shares a word).  A reader would never cite it.
  PASS 2 (criterion) -- the title shares the paper's words AND is in software, but names an ADJACENT
                        construct: detection of malicious packages rather than what a declaration
                        determines; web-API versioning rather than version ranges; product-line
                        variability rather than dependency resolution.  These are the expensive ones,
                        because they look right.

RULES ARE PREDICATES OVER THE TITLE, NOT A LIST OF KEYS.  The sibling package (#145) recorded its
rejections as hand-copied keys and 28 of them matched nothing, because the keys came from a truncated
print.  A predicate states *why* a record is out, applies to every record, and prints what it caught --
so the rule is auditable and a re-harvest cannot smuggle a record past it.

Every rejection is recorded WITH ITS REASON and the record STAYS in the corpus marked `excluded`, so a
reader sees what was considered and refused rather than only what survived.

Usage: python3 review_references.py [--show] [--out refs/references.json]
"""
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CORPUS = os.path.join(HERE, "refs", "references.json")

# ---------------------------------------------------------------- PASS 1: salience
# A match here means the title is about another field entirely.  Each rule names the homonym it catches.
PASS1 = [
    ("ferro-pinning", r"domain wall|ferromagn|nanowire|magnetic (domain|pinning)|superconduct",
     "PASS 1, homonym: 'pinning' is magnetic domain-wall pinning, not version pinning"),
    ("biology-dependency", r"pyridoxine|gene network|dna|protein|clinical|patient|\bcancer\b|tumou?r|"
                           r"melanoma|haematolog|cutaneous|pharmacolog|snp filter|bioinformatic",
     "PASS 1, different field: the title shares a word with the topic and is a biological/medical study"),
    ("public-health-ecosystem", r"human health|ecosystem health|epidemi|public health|well-?being",
     "PASS 1, different field: 'ecosystem' in the public-health sense"),
    ("linguistics-dependency", r"dependency pars|dependency grammar|syntactic|reordering model|"
                               r"relation extraction|head-modifier",
     "PASS 1, homonym: 'dependency' in the dependency-grammar sense"),
    ("statistical-dependence", r"radionuclide|waste package|finite element|turbulen|"
                               "groundwater",
     "PASS 1, different field: a physical/engineering study"),
    ("front-matter", r"copyright|^cover$|\btoc\b|\btitle page|^research metrics from|"
                     r"session xiv|^metadata repository$|^constraint satisfaction problem$|"
                     r"^hybrid tractability$|^distributed constraint satisfaction problem$",
     "PASS 1, not a standalone work: front matter / an index entry Crossref records as a work"),
    ("archival-repository", r"digital repository|national library|music|mei data|archive of|"
                            "archeology|screen4care",
     "PASS 1, homonym: 'repository' in the library-archive sense, not a package registry"),
    ("psychology-manifest", r"manifest anxiety|task performance|plant sciences|shenzhen declaration",
     "PASS 1, homonym: 'manifest' in the psychology/political-declaration sense"),
    ("telecom-registry", r"mediacontrol|interactive voice response|iana registry",
     "PASS 1, homonym: 'registry' in the protocol-registry sense"),
    ("blockchain", r"blockchain|ark\b|token market|smart contract|decentraliz",
     "PASS 1, different field: a distributed-ledger study, not a package registry"),
    ("medicine-outdated", r"cardiac|rehabilitation|patient care|clinical trial|dosage",
     "PASS 1, different field: 'outdated version' here names a clinical guideline, not a package"),
    ("image-tag", r"image ranking|tag image file format|tiff|image retrieval|image classif|"
                  r"remote sensing",
     "PASS 1, homonym: 'tag'/'version' in image formats and retrieval, not a registry tag"),
    ("criminology", r"\bcrime\b|criminal|offend|policing",
     "PASS 1, different field: a criminology study that contains the word 'update'"),
    ("hydrology", r"stream drift|hydrolog|sediment|groundwater|rainfall|watershed",
     "PASS 1, homonym: 'drift' in hydrology, not version drift"),
    ("genomics", r"genom|phylogen|sequence alignment|proteom|transcriptom|variant calling",
     "PASS 1, different field: a genomics study"),
    ("or-optimisation", r"buffer allocation|bin packing|facility location|vehicle routing|"
                        "simulation-based optimisation|scheduling problem|supply chain network design",
     "PASS 1, different field: operations-research optimisation. 'Solving' here is not package solving"),
    ("ml-concept-drift", r"concept drift|data drift|distribution shift",
     "PASS 1, homonym: 'drift' in the machine-learning sense (distribution shift), not version drift"),
    ("climate-tooling", r"climate model|resource usa|simulation of",
     "PASS 1, adjacent population: domain-science tooling rather than a study of declarations"),
    ("xml-numbering", r"numbering scheme on xml|dynamic xml trees|preorder numbering",
     "PASS 1, homonym: a tree-numbering scheme for XML storage, not a package version number"),
    ("biology-numbering", r"scramblase|tmem\d|membrane protein",
     "PASS 1, homonym: 'numbering scheme' for a protein family, not a version scheme"),
    ("db-dependency-theory", r"multivalued dependenc|transaction closures|relational database|"
                              r"database theory|functional dependenc",
     "PASS 1, adjacent theory: database dependency theory. Same word ('dependency'), different object "
     "-- schema constraints, not package versions"),
    ("authz-policy", r"authorization polic|access control polic|web services in presence",
     "PASS 1, adjacent construct: security policy composition, not dependency resolution"),
    ("logic-programming", r"normal programs|smodels|logic programming|declarative diagnosis|"
                          r"answer set|prolog",
     "PASS 1, homonym: 'declarative' in logic programming, not a declarative dependency manifest"),
    ("graph-bundles", r"cartesian graph bundles|graph bundle",
     "PASS 1, different field: a graph-theory construction the relevance gate matched on 'graph'"),
    ("evidence-resolution", r"repair evidence|structural resolution",
     "PASS 1, homonym: 'resolution' in a program-repair / computation-model sense"),
    ("network-config", r"network device configuration|router configuration|policy configuration",
     "PASS 1, adjacent population: network configuration correctness, not package resolution"),


]

# ---------------------------------------------------------------- PASS 2: criterion
# A match here means the record is in software but names an adjacent construct the paper does not use.
PASS2 = [
    ("web-api-versioning", r"rest api|web api|web service clients|spring boot|^versioning the api$|"
                           r"api versioning practices",
     "PASS 2, adjacent construct: HTTP/web API versioning, not a package manager's version RANGE -- the "
     "paper's unit is a declared range over registry versions, not an endpoint's compatibility policy"),
    ("api-field-evolution", r"android api|python/c api|framework api evolution|change rules",
     "PASS 2, adjacent construct: source-level API evolution, which studies signature changes rather "
     "than what a declaration leaves open"),
    ("detection-estimand", r"malicious|typosquat|detector|attack detection|vulnerabilit(y|ies) detection|"
                           "llm-based detection|prompt engineering",
     "PASS 2, adjacent estimand: detection of bad packages. The population overlaps, but the quantity "
     "is detector accuracy, not what a declaration determines"),
    ("vuln-propagation", r"vulnerability propagation|security vulnerabilit|exploit|advisory",
     "PASS 2, adjacent estimand: vulnerability reachability rather than declaration determinacy"),
    ("product-line", r"feature model|product line|product-line|variability-aware|software product",
     "PASS 2, adjacent construct: feature-model configuration in product lines. Same word ('selection'), "
     "different object -- compile-time features, not registry versions"),
    ("requirements-graph", r"requirements dependency|requirements specification|design pattern|"
                           "private cloud|microservice call graph|cloud failure",
     "PASS 2, adjacent construct: requirements/architecture dependency graphs, which are not resolution "
     "constraints"),
    ("software-announcement", r"citation\.js|^sbml level|r package for|a julia package for|"
                              "^biocpkgtools|^pvac:",
     "PASS 2, not a study: a software package announcement or its documentation"),
    ("tool-for-biology", r"quantitative systems pharmacology|distributed acoustic sensing|"
                         "snp filtering|ros 1 and ros 2 bags",
     "PASS 2, adjacent population: a domain-science tool packaged for reproducibility, not a study of "
     "what declarations determine"),
    ("csp-classification", r"data cleaning via constraint|regular constraint|groupoid|conjunctive quer|"
                           "smooth constraint|constraint satisfaction optimization problem|"
                           "distributed constraint satisfaction",
     "PASS 2, adjacent instrument: generic CSP work that does not bear on the identifying-set argument. "
     "The tractability results that DO bear on it are kept"),
    ("ml-package-type", r"machine learning approach to determine|classifier|categorizer|"
                        "deep approximation|metaheuristic",
     "PASS 2, adjacent method: predicting a label (e.g. the semver type) rather than measuring what a "
     "declaration determines"),
    ("bioinformatics-tooling", r"galaxy tool|galaxy platform|bioinformatic|bioconductor|conda as|"
                               r"dependencies in computational biology",
     "PASS 2, adjacent population: bioinformatics tooling commentary, not a registry-resolution study"),
    ("cps-config", r"cyber physical|cyber-physical",
     "PASS 2, adjacent population: CPS integration, not registry resolution"),
]


def norm(s):
    return re.sub(r"\s+", " ", (s or "")).strip()


def classify(entry):
    """(verdict, reason, pass) -- first matching rule wins, and the pass is recorded."""
    t = norm(entry.get("title")).lower()
    for rid, pat, why in PASS1:
        if re.search(pat, t):
            return "excluded", "%s [rule %s]" % (why, rid), 1
    for rid, pat, why in PASS2:
        if re.search(pat, t):
            return "excluded", "%s [rule %s]" % (why, rid), 2
    return "kept", "", 0


def main():
    out = CORPUS
    if "--out" in sys.argv:
        out = sys.argv[sys.argv.index("--out") + 1]
    d = json.load(io.open(out, encoding="utf-8"))
    entries = d["entries"]
    tally = {}
    for e in entries:
        # A REMOVAL IS A DECISION, NOT A DERIVED VERDICT. `build_references.py --remove` marks an
        # entry `removed` with a reason; re-running the review must not recompute it back to
        # `kept`, or the removal silently undoes itself the next time anyone rebuilds the corpus
        # (measured: an entry removed for having no corroborating field came back as kept after
        # one re-run). Derived verdicts are recomputed; recorded decisions are carried.
        if e.get("review") == "removed":
            tally.setdefault(("removed", "recorded removal, reason kept"), 0)
            tally[("removed", "recorded removal, reason kept")] = \
                tally[("removed", "recorded removal, reason kept")] + 1
            continue
        verdict, reason, ps = classify(e)
        e["review"] = verdict
        e["review_reason"] = reason
        e["review_pass"] = ps
        tally.setdefault((ps, reason.split(" [rule ")[0][:60] if reason else "kept"), 0)
        tally[(ps, reason.split(" [rule ")[0][:60] if reason else "kept")] = \
            tally[(ps, reason.split(" [rule ")[0][:60] if reason else "kept")] + 1

    kept = [e for e in entries if e["review"] == "kept"]
    ex1 = [e for e in entries if e["review"] == "excluded" and e.get("review_pass") == 1]
    ex2 = [e for e in entries if e["review"] == "excluded" and e.get("review_pass") == 2]

    # per-query survival: a query whose ENTIRE yield was refused is a bad query and is named as one
    by_q = {}
    for e in entries:
        by_q.setdefault(e.get("query") or "verified", [0, 0])
        by_q[e.get("query") or "verified"][0] += 1
        if e["review"] == "kept":
            by_q[e.get("query") or "verified"][1] += 1
    dead = sorted(q for q, (n, k) in by_q.items() if n and k == 0 and q != "verified")

    d["review"] = {
        "method": "two passes: salience (other field) then criterion (adjacent construct); rules are "
                  "predicates over the title, applied to every record",
        "mechanical": len(entries), "kept": len(kept),
        "excluded_pass1": len(ex1), "excluded_pass2": len(ex2),
        "excluded_total": len(ex1) + len(ex2),
        "rejection_rate": (float(len(ex1) + len(ex2)) / len(entries)) if entries else None,
        "queries_with_no_surviving_record": dead,
        "per_query": dict((q, {"considered": n, "kept": k}) for q, (n, k) in sorted(by_q.items())),
    }
    io.open(out, "w", encoding="utf-8").write(json.dumps(d, indent=1, sort_keys=True) + "\n")

    print("mechanical corpus : %d" % len(entries))
    print("pass 1 excluded   : %d  (other field entirely)" % len(ex1))
    print("pass 2 excluded   : %d  (in software, adjacent construct)" % len(ex2))
    print("kept              : %d" % len(kept))
    print("rejection rate    : %.3f" % d["review"]["rejection_rate"])
    print("queries whose whole yield was refused: %d %s"
          % (len(dead), dead if dead else ""))
    print("\nby rule:")
    for (ps, why), n in sorted(tally.items(), key=lambda x: (-x[1], x[0])):
        if n:
            print("  pass %d  %-58s %3d" % (ps, why[:58], n))
    if "--show" in sys.argv:
        print("\nexcluded, with reason:")
        for e in sorted(entries, key=lambda x: (x.get("review_pass") or 0, x.get("title") or "")):
            if e["review"] == "excluded":
                print("  [p%d] %-70s %s" % (e.get("review_pass") or 0,
                                            (e.get("title") or "")[:70], e.get("review_reason"))[:200])
    return 0


if __name__ == "__main__":
    sys.exit(main())
