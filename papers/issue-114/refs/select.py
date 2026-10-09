#!/usr/bin/env python3
"""Select the reference list from the matched candidates, with every rejection GIVEN A REASON.

`build_refs.py` screens by title overlap, and a screen is not a decision: its accepted set
contains false matches -- a query about specification/implementation co-evolution matched a
record titled "Specification and Implementation", and a query about software brittleness
matched a paper on software product quality measurement.  Citing those would be worse than
citing nothing, because they LOOK verified: the record exists, it is simply not the work the
sentence claims.

So this file is the human decision layer.  It holds REJECT (key -> why) and RENAME (key ->
better key), and it emits `selection.json`: the entries that a sentence may cite, each with
the reason it was kept.  Every rejection is a permanent record of a near-miss.

Usage: python3 select.py     (writes selection.json; prints the accepted list)
"""

from __future__ import annotations

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

# A matched record that must NOT become a citation, with the reason it is not the work the
# query named.  These are the near-misses a score cannot separate from a hit.
REJECT = {
    "sel4": "matched 'Is Formal Verification of seL4 Adequate...', not the seL4 SOSP paper",
    "isabelle": "matched a program-logic paper about Isabelle, not the Isabelle/HOL book",
    "liquidtypes": "matched 'Liquid Crystals: Main Types and Classification' -- a chemistry paper",
    "fmstate": "matched a book titled '...State of the Art and New Directions', not the roadmap paper",
    "fmpractice": "matched a teaching-index record, not the practice-and-experience survey",
    "metacacm": "matched a metamorphic-testing-for-ML paper, not the CACM review",
    "mldatavalidation": "matched a geospatial cross-validation paper; the query was a topic phrase, not a title",
    "specificationpatterns": "matched an unrelated tools paper",
    "monitorlearning": "matched an artificial-pancreas verification paper; duplicates rvmonitor's query",
    "testoraclellm": "matched an LLM test-case-generation paper, not an oracle-generation one",
    "aprbiblio": "matched 'Automatic Software Repair' -- ambiguous with aprsurvey, not the bibliography",
    "softwareaging": "record carries no year and the title is a fragment ('Software aging')",
    "churndefects": "record carries no year; a citation needs one",
    "equivalencetesting": "matched a book on digital-circuit equivalence, not program equivalence",
    "propchecking": "matched a PropEr integration paper; cite that work, not a book by that name",
    "covolution": "matched 'Specification and Implementation' -- a different work entirely",
    "alloyfindbugs": "matched a copy-paste-detection paper",
    "theoryofbrittle": "matched a software-quality-measurement paper, not a brittleness study",
    "spin": "matched 'Parallelizing the Spin Model Checker', not Holzmann's SPIN paper",
    "null": "no such work",
    "ossdoc": "no such work",
    "metascience": "query was a placeholder; no such work",
    "fuzzing": "query was a placeholder; no such work",
    "behavioralequiv": "query was a placeholder; no such work",
    "specevolution": "matched an SOA maintenance paper",
    "coq": "the Coq manual is not a citable record in this index",
    "runtimeverification": "matched an introduction chapter; the survey is rvmonitor",
}

# Keys whose record is real but whose key was a placeholder: give them a name that says what
# they are, so the manuscript's citation reads sensibly.
RENAME = {
    "jbding": "abstractionrefinement",
    "contractrefine": "refinementtypes",
    "propchecking": "proper",
    "theoryofbrittle": "qualitymeasurement",
    "equivalencetesting": "circuitequivalence",
}

# The one-line difference this paper states against a reference.  Only the entries the
# manuscript actually compares against need one (the journal requires >=3 stated differences;
# the rest are citation-support and carry a short note of WHY they are cited).
DIFFERENCES = {
    "non-testable": "introduced the oracle problem for programs with no expected output; we do not need an oracle because our semantics is decidable",
    "oraclesurvey": "catalogues oracle-construction techniques; we ask a different question -- what a specification's own STRENGTH costs",
    "mutasurvey": "measures mutants' fault-detection power; we use mutations as a controlled change population to price a specification",
    "mutationsurvey": "the standard survey of mutation testing; we invert it -- mutants are our instruments, not our object of study",
    "equivmutants": "detects equivalent mutants by compiler optimisation, case by case; our oracle decides equivalence over the whole input domain by construction",
    "aremutants": "asks whether mutants substitute for real faults; we ask what a specification's shape implies about which changes it will catch",
    "trivialequiv": "a large-scale empirical study of equivalent-mutant detection; our ground truth is exact and needs no detector",
    "qedatlarge": "documents proof-engineering cost and maintenance; we make the cost of REPRESENTATION a measurable axis",
    "awsformal": "industrial evidence that formal methods pay off at scale; we ask when a stronger specification stops paying",
    "wing": "the classical formal-methods primer; it treats specification strength as monotone, which is what we test",
    "fmstate": "the roadmap paper; it names specification maintenance as open without measuring it",
    "awsformal": "industrial evidence; we quantify the trade-off it reports anecdotally",
    "clarke": "state of the art; treats elaboration as free",
    "tamingfuzzers": "tests compilers against a reference; we test specifications against a decidable semantics",
    "findingbugs": "differential testing of compilers; a change population of the same kind, without a specification axis",
    "translatevalid": "proves a compiler transformation equivalent; we ask what a specification can DETECT about one",
    "valuegraph": "translation validation at scale; same question, compiler-specific instrument, no strength axis",
    "flakysurvey": "flaky tests as a symptom of brittleness; we make the brittleness a designed axis rather than a discovered symptom",
    "flakypython": "same, in Python; our change population is generated, so the brittleness is not a property of one repository",
    "regressionsurvey": "prices test suites by cost and detection; we price a specification by detection AND false alarms",
    "prioritization": "orders tests; we order specifications by net value at a given change rate",
    "mltestingsurvey": "documents ML testing practice; a different notion of specification (data, not code)",
    "hiddendebt": "names technical debt in ML systems; we make one class of it -- representation coupling -- measurable",
    "samplingse": "how to sample a population for SE research; we enumerate our population and report bands instead",
    "expguidelines": "the standard empirical-methodology guidelines; our controls are built to its spirit",
    "tichy": "argues for experiment in CS; this paper is an experiment on specifications",
    "daikon": "infers invariants from executions -- a specification PROPOSER; we study what a given specification costs",
    "daikonsystem": "the Daikon implementation; our specs are constructed from a generator, not inferred",
}


def main() -> int:
    raw = json.load(open(os.path.join(HERE, "build_refs_out.json")))
    accepted, rejected = [], list(REJECT.items())
    seen_keys = set()
    for p in raw["picks"]:
        k = p["key"]
        if k in REJECT:
            continue
        new_key = RENAME.get(k, k)
        if new_key in seen_keys:
            rejected.append((k, "duplicate key after rename"))
            continue
        seen_keys.add(new_key)
        accepted.append({
            "key": new_key,
            "title": p["title"],
            "year": p["year"],
            "venue": p["venue"],
            "doi": p["doi"],
            "authors": p["authors"],
            "source": "crossref",
            "match_score": p["match_score"],
            "query": p["query"],
            "difference": DIFFERENCES.get(new_key, ""),
        })

    # entries in the RENAME table that were rejected must not silently vanish
    for k, why in REJECT.items():
        if k not in {p["key"] for p in raw["picks"]} and k not in RENAME:
            pass

    with open(os.path.join(HERE, "selection.json"), "w") as fh:
        json.dump({"accepted": accepted, "rejected": [{"key": k, "why": w} for k, w in rejected],
                   "unmatched": raw["unmatched"]}, fh, indent=1)

    print(f"accepted {len(accepted)}  rejected {len(rejected)}  unmatched {len(raw['unmatched'])}")
    for a in accepted:
        print(f"  {a['key']:<22} {str(a['year'])[:4]:<5} {a['title'][:70]}")
    print()
    print("REJECTED (near-misses, kept as a record):")
    for k, w in rejected:
        print(f"  {k:<22} {w}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
