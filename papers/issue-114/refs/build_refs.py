#!/usr/bin/env python3
"""Build the reference list: name candidates, let Crossref/arXiv FIND and CONFIRM each.

WHY THIS SHAPE
--------------
The journal requires every reference to be verified against a real record, and requires the
verification to be recorded.  Two ways to get candidates are available, and they fail
differently:

  * keyword harvest (see `harvest.py`) -- everything returned EXISTS, but topical search is
    noisy, so selecting from it is a relevance problem; and
  * named candidates (this file) -- the risk is that my memory of a title/author/year is
    approximate, so the API must be allowed to REFUSE.

This script takes the second route and makes the refusal explicit: each named candidate is a
QUERY, the response is scored by token overlap with the query, and a candidate whose best
match scores below the threshold is written to `refs_unmatched.json` instead of into the list.
A query that Crossref cannot resolve never becomes a citation -- there is no path here that
emits an unverified entry.  (The recent arXiv entries come from the topical harvest and are
carried by identifier, so they are located rather than searched for.)

Usage: python3 build_refs.py      (writes refs_raw.json, refs_unmatched.json, refs_picks.json)
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, "search_cache")
os.makedirs(CACHE, exist_ok=True)

# Path A: named candidates. `key` is the citation key used in the manuscript; the string is
# the QUERY, not a claim about the record -- the API supplies author/year/venue/DOI.
CANDIDATES = [
    # --- the oracle problem, testing foundations -------------------------------------
    ("non-testable", "On testing non-testable programs Weyuker"),
    ("oraclesurvey", "The Oracle Problem in Software Testing: A Survey Barr Harman McMinn Shahbaz Yoo"),
    ("metacacm", "Metamorphic Testing: A Review of Challenges and Opportunities Chen Cheung Yiu"),
    ("metasurvey", "A Survey on Metamorphic Testing Segura Fraser Sanchez Ruiz-Cortes"),
    ("quickcheck", "QuickCheck: a lightweight tool for random testing of Haskell programs Claessen Hughes"),
    ("korat", "Korat: automated testing based on Java predicates Boyapati Khurshid Marinov"),
    ("feedbackrandom", "Feedback-directed random test generation Pacheco Lahiri Ernst Ball"),
    ("dart", "DART: directed automated random testing Godefroid Klarlund Sen"),
    ("klee", "KLEE: unassisted and automatic generation of high-coverage tests for complex systems programs"),
    ("tamingfuzzers", "Taming compiler fuzzers Chen Groce Zhang Wong Fern Eide Regehr"),
    ("findingbugs", "Finding and understanding bugs in C compilers Yang Chen Eide Regehr"),
    # --- mutation testing ------------------------------------------------------------
    ("mutationsurvey", "An Analysis and Survey of the Development of Mutation Testing Jia Harman"),
    ("mutationadvances", "Mutation Testing Advances: An Analysis and Survey Papadakis Kintis Zhang Jia Traon Harman"),
    ("hints", "Hints on Test Data Selection: Help for the Practicing Programmer DeMillo Lipton Sayward"),
    ("equivmutants", "Using compiler optimization techniques to detect equivalent mutants Offutt Craft"),
    ("aremutants", "Are mutants a valid substitute for real faults in software testing Just Jalali Inozemtseva Ernst Holmes Fraser"),
    ("trivialequiv", "Trivial Compiler Equivalence: A Large Scale Empirical Study of a Simple, Fast and Effective Equivalent Mutant Detection Technique"),
    ("threatsvalidity", "Threats to the validity of mutation-based test assessment Papadakis Jia Harman"),
    ("impactequiv", "The Impact of Equivalent Mutants Gruen Schuler"),
    ("secondorder", "Isolating First Order Equivalent Mutants via Second Order Mutation Kintis Papadakis Malevris"),
    # --- specification, refinement, formal methods -----------------------------------
    ("hoare", "An axiomatic basis for computer programming Hoare"),
    ("guarded", "Guarded commands, nondeterminacy and formal derivation of programs Dijkstra"),
    ("refinementcalc", "Refinement Calculus: A Systematic Introduction Back von Wright"),
    ("bbook", "The B-Book: Assigning Programs to Meanings Abrial"),
    ("alloy", "Alloy: a lightweight object modelling notation Jackson"),
    ("tla", "Specifying Systems: The TLA+ Language and Tools for Hardware and Software Engineers Lamport"),
    ("awsformal", "How Amazon Web Services Uses Formal Methods Newcombe Rath Zhang Munteanu Brooker Deardeuff"),
    ("fmpractice", "Formal methods: practice and experience Woodcock Larsen Bicarregui Fitzgerald"),
    ("wing", "A specifier's introduction to formal methods Wing"),
    ("fmstate", "Formal methods: state of the art and future directions Clarke Wing"),
    ("designbycontract", "Applying design by contract Meyer"),
    ("jml", "JML: A Notation for Detailed Design Leavens Baker Ruby"),
    ("modelbasedtesting", "Practical Model-Based Testing: A Tools Approach Utting Legeard"),
    # --- proof engineering and verified software -------------------------------------
    ("qedatlarge", "QED at Large: A Survey of Engineering of Formally Verified Software Ringer Palmskog Sergey Gligoric Tatlock"),
    ("adaptingproof", "Adapting proof automation to adapt proofs Ringer Yazdani Leo Grossman"),
    ("compcert", "Formal verification of a realistic compiler Leroy"),
    ("sel4", "seL4: formal verification of an OS kernel Klein Elphinstone Heiser Andronick Cock Derrin"),
    ("kepler", "A formal proof of the Kepler conjecture Hales Adams Bauer Dang Harrison"),
    ("fourcolor", "Formal Proof - The Four-Color Theorem Gonthier"),
    ("translatevalid", "Translation validation for an optimizing compiler Necula"),
    ("valuegraph", "Evaluating value-graph translation validation for LLVM Tristan Govereau Morrisett"),
    ("verificationcost", "A Survey of Automated Techniques for Formal Software Verification DSilva Kroening Weissenbacher"),
    ("slamsdecade", "A decade of software model checking with SLAM Ball Levin Rajamani"),
    ("swnodechecking", "Software model checking Jhala Majumdar"),
    ("spin", "The model checker SPIN Holzmann"),
    # --- regression, flakiness, change ------------------------------------------------
    ("regressionsurvey", "Regression testing minimization, selection and prioritization: a survey Yoo Harman"),
    ("rtssurvey", "Analyzing regression test selection techniques Rothermel Harrold"),
    ("prioritization", "Test case prioritization: a family of empirical studies Elbaum Malishevsky Rothermel"),
    ("flakysurvey", "An empirical analysis of flaky tests Luo Hariri Eloussi Marinov"),
    ("flakypython", "An Empirical Study of Flaky Tests in Python Gruber Lukasczyk Kroiss Fraser"),
    ("googleci", "Taming Google-Scale Continuous Testing Memon Gao Nguyen"),
    ("genprog", "GenProg: A Generic Method for Automatic Software Repair Le Goues Nguyen Forrest Weimer"),
    ("aprsurvey", "Automatic Software Repair: A Survey Gazzola Micucci Mariani"),
    ("aprbiblio", "Automatic software repair: a bibliography Monperrus"),
    # --- dynamic invariants / specification inference ---------------------------------
    ("daikon", "Dynamically discovering likely program invariants to support program evolution Ernst Cockrell Griswold Notkin"),
    ("daikonsystem", "The Daikon system for dynamic detection of likely invariants Ernst Perkins Guo McCamant Pacheco Tschantz Xiao"),
    ("agitator", "From Daikon to Agitator: lessons and challenges in building a commercial tool for developer testing Boshernitsan Doong Savoia"),
    # --- evolution, churn, complexity -------------------------------------------------
    ("softwareaging", "Software Aging Parnas"),
    ("lehman", "Programs, life cycles, and laws of software evolution Lehman"),
    ("churndefects", "Use of relative code churn measures to predict system defect density Nagappan Ball"),
    ("complexityfaults", "Predicting faults using the complexity of code changes Hassan"),
    ("changedistilling", "Change Distilling: Tree Differencing for Fine-Grained Source Code Change Extraction Fluri Wuersch Pinzger Gall"),
    ("tangled", "The impact of tangled code changes Herzig Zeller"),
    ("metricsvalidation", "A Validation of Object-Oriented Design Metrics as Quality Indicators Basili Briand Melo"),
    ("ckmetrics", "A metrics suite for object oriented design Chidamber Kemerer"),
    # --- empirical method in software engineering ------------------------------------
    ("expguidelines", "Preliminary Guidelines for Empirical Research in Software Engineering Kitchenham Pfleeger Pickard Jones Hoaglin El Emam Rosenberg"),
    ("empiricalstandards", "Empirical Standards for Software Engineering Research Ralph Baltes Bianculli"),
    ("samplingse", "Sampling in software engineering research: a critical review and guidelines Baltes Ralph"),
    ("tichy", "Should computer scientists experiment more Tichy"),
    ("experimentation", "Experimentation in Software Engineering Wohlin Runeson Host Ohlsson Regnell"),
    ("metascience", "A Large-Scale Study of the Software Engineering Research Landscape"),
    # --- ML systems, brittleness of learned components -------------------------------
    ("hiddendebt", "Hidden Technical Debt in Machine Learning Systems Sculley Holt Golovin Davydov Phillips"),
    ("mltestscore", "The ML Test Score: A Rubric for ML Production Readiness and Technical Debt Reduction Breck Cai Nielsen Salib Sculley"),
    ("mltestingsurvey", "Machine Learning Testing: Survey, Landscapes and Horizons Zhang Harman Ma Liu Inoue"),
    ("mldeploysurvey", "Challenges in Deploying Machine Learning: a Survey of Case Studies Paleyes Urma Lawrence"),
    ("mldatavalidation", "Data Validation for Machine Learning Breck Polyzotis Roy Whang Zinkevich"),
    # --- runtime verification, monitors ---------------------------------------------
    ("runtimeverification", "Introduction to the special section on runtime verification Bartocci Falcone Francalanza Reger"),
    ("rvmonitor", "A survey of challenges for runtime verification from advanced application domains"),
    # --- semantics, equivalence, refinement in practice -----------------------------
    ("equivalencetesting", "Equivalence checking of sequential circuits"),
    ("behavioralequiv", "Behavioral equivalence and the semantics of programs"),
    ("propchecking", "Property-Based Testing with PropEr, Erlang, and Elixir"),
    ("fuzzing", "Coverage-guided fuzzing as a software testing technique survey"),
    ("smtbasedverif", "Satisfiability Modulo Theories: Introduction and Applications Barrett Sebastiani Seshia Tinelli"),
    ("why3", "Why3: Where Programs Meet Provers Filliatre Paskevich"),
    ("frama-c", "Frama-C: A software analysis perspective Kirchner Kosmatov Prevosto Signoles Yakobowski"),
    ("dafny", "Dafny: An Automatic Program Verifier for Functional Correctness Leino"),
    ("coq", "The Coq proof assistant reference manual"),
    ("isabelle", "Isabelle/HOL: A Proof Assistant for Higher-Order Logic Nipkow Paulson Wenzel"),
    ("lean", "The Lean Mathematical Library mathlib: building a community library"),
    # --- specification evolution / co-evolution --------------------------------------
    ("specevolution", "Specification evolution and its impact on software maintenance"),
    ("covolution", "Co-evolution of specification and implementation"),
    ("alloyfindbugs", "Finding bugs in software with Alloy"),
    ("jbding", "Abstraction Refinement for Large Scale Model Checking"),
    ("contractrefine", "Refinement types for Haskell Vazou Seidel Jhala Vytiniotis Peyton Jones"),
    ("liquid", "Liquid Types Rondon Kawauchi Jhala"),
    ("gradualtypes", "Gradual Typing for Functional Languages Siek Taha"),
    ("blame", "Well-typed programs can't be blamed Wadler Findler"),
    ("theoryofbrittle", "Software brittleness and its measurement"),
    ("ossdoc", "Software documents: concepts and tools"),
    ("null", "The Null Pointer Reference Problem"),
]

# Path A2: the second pass.  The first pass put AUTHOR SURNAMES in the query, which a
# bibliographic index does not index against the title, so several well-known works scored
# below the screen while an unrelated record scored above it.  These are title-only queries.
SECOND_PASS = [
    ("quickcheck", "QuickCheck: a lightweight tool for random testing of Haskell programs"),
    ("korat", "Korat: automated testing based on Java predicates"),
    ("dart", "DART: directed automated random testing"),
    ("klee", "KLEE: unassisted and automatic generation of high-coverage tests for complex systems programs"),
    ("alloy", "Alloy: a lightweight object modelling notation"),
    ("bbook", "The B-Book: Assigning Programs to Meanings"),
    ("sel4", "seL4: formal verification of an OS kernel"),
    ("hiddendebt", "Hidden Technical Debt in Machine Learning Systems"),
    ("empiricalstandards", "Empirical Standards for Software Engineering Research"),
    ("isabelle", "Isabelle/HOL: A Proof Assistant for Higher-Order Logic"),
    ("liquidtypes", "Liquid types"),
    ("gradualtypes", "Gradual Typing for Functional Languages"),
    ("fmstate", "Formal methods: state of the art and future directions"),
    ("fmpractice", "Formal methods: practice and experience"),
    ("modelbasedtesting", "Practical Model-Based Testing: A Tools Approach"),
    ("refinementcalc", "Refinement Calculus: A Systematic Introduction"),
    ("metacacm", "Metamorphic Testing: A Review of Challenges and Opportunities"),
    ("mutationadvances", "Mutation Testing Advances: An Analysis and Survey"),
    ("agitator", "From Daikon to Agitator: lessons and challenges in building a commercial tool"),
    ("mldatavalidation", "Data Validation for Machine Learning"),
    ("modularity", "On the criteria to be used in decomposing systems into modules"),
    ("silverbullet", "No Silver Bullet: Essence and Accidents of Software Engineering"),
    ("specificationpatterns", "Specification patterns for formal software verification"),
    ("monitorlearning", "A survey of challenges for runtime verification"),
    ("proofrepair", "Program repair for proofs: a formal framework for proof repair"),
    ("verifycost", "The economics of formal verification"),
    ("analysisoss", "Large-scale study of the adoption of formal methods in open source"),
    ("testoraclellm", "Large language models for test oracle generation"),
    ("mutationllm", "Mutation testing of large language model generated code"),
    ("assertmining", "Mining specifications from source code"),
]

# Path B: recent entries carried by identifier, chosen from the topical harvest for
# currency -- these exist by construction and are verified by id in `verify_refs.py`.
RECENT_BY_ID = [
    "2609.00000",   # placeholder keys are dropped automatically if they do not resolve
]


def norm(s: str) -> str:
    return re.sub(r"[^a-z0-9 ]+", " ", s.lower())


def score(query: str, title: str, authors=()) -> float:
    """Token overlap between the query and the record's TITLE.

    The query in `CANDIDATES` ends with author surnames, which a bibliographic index does not
    put in the title -- so scoring the raw query penalised exactly the records that were right
    (the oracle-problem survey scored 0.55 for having the authors in the query).  Tokens that
    appear in the returned author list are therefore removed from the DENOMINATOR: what is
    measured is how much of the query's TITLE survives in the record's title.
    """
    q = [w for w in norm(query).split() if len(w) > 2]
    author_tokens = set()
    for a in authors:
        author_tokens |= set(norm(f"{a.get('family', '')} {a.get('given', '')}").split())
    denom = [w for w in q if w not in author_tokens]
    t = set(norm(title).split())
    if not denom:
        return 0.0
    return sum(1 for w in denom if w in t) / len(denom)


def crossref(query: str, rows: int = 5):
    q = urllib.parse.quote(query)
    url = (f"https://api.crossref.org/works?query.bibliographic={q}&rows={rows}"
           f"&select=DOI,title,author,issued,container-title,type")
    cache = os.path.join(CACHE, re.sub(r"[^a-z0-9]+", "_", query.lower())[:80] + ".json")
    if os.path.exists(cache):
        return json.load(open(cache))
    req = urllib.request.Request(url, headers={
        "User-Agent": "issue-114-bibliography/1.0 (mailto:noreply@example.org)"})
    try:
        with urllib.request.urlopen(req, timeout=45) as r:
            d = json.loads(r.read().decode("utf-8", "replace"))
    except Exception as exc:                       # noqa: BLE001 - network failure is recorded
        print(f"    !! {type(exc).__name__}: {exc}", file=sys.stderr)
        return None
    json.dump(d, open(cache, "w"))
    time.sleep(0.3)
    return d


def main() -> int:
    picks, unmatched = [], []
    seen_keys = set()
    for key, query in CANDIDATES + SECOND_PASS:
        if key in seen_keys:
            continue
        d = crossref(query)
        if d is None:
            unmatched.append({"key": key, "query": query, "why": "network"})
            continue
        items = d["message"]["items"]
        best, best_s = None, 0.0
        for it in items:
            t = (it.get("title") or [""])[0].strip()
            if not t:
                continue
            s = score(query, t, it.get("author") or [])
            if s > best_s:
                best, best_s = it, s
        if best is None or best_s < 0.75:
            unmatched.append({"key": key, "query": query,
                              "why": f"best match {best_s:.2f}",
                              "best_title": (best.get("title") or [""])[0] if best else None})
            continue
        yr = (best.get("issued", {}).get("date-parts") or [[None]])[0][0]
        ct = best.get("container-title") or [""]
        if key in {p["key"] for p in picks}:
            continue
        seen_keys.add(key)
        picks.append({
            "key": key, "query": query, "match_score": round(best_s, 3),
            "doi": best.get("DOI", ""), "title": best.get("title", [""])[0].strip(),
            "year": yr, "venue": (ct[0] if ct else ""), "type": best.get("type", ""),
            "authors": [{"family": a.get("family", ""), "given": a.get("given", "")}
                        for a in (best.get("author") or [])],
        })
        print(f"  {key:<20} {best_s:.2f}  {picks[-1]['year']}  {picks[-1]['title'][:70]}")

    json.dump({"picks": picks, "unmatched": unmatched},
              open(os.path.join(HERE, "build_refs_out.json"), "w"), indent=1)
    print(f"\nmatched {len(picks)} / {len(CANDIDATES)} candidates; {len(unmatched)} unmatched")
    for u in unmatched:
        print(f"  UNMATCHED {u['key']:<20} ({u['why']}) {u.get('best_title') or ''}"[:120])
    return 0


if __name__ == "__main__":
    sys.exit(main())
