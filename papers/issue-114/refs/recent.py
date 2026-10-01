#!/usr/bin/env python3
"""Add the recent (arXiv) entries to the selection.

These come from the TOPICAL harvest, so they are located by identifier rather than searched
for: the record is read out of the arXiv response itself, which means author/title/year are
the publisher's own values and cannot be a paraphrase of mine.  What the selection decides
here is only RELEVANCE -- which of the harvested works the paper actually cites.

Every id below was printed from `candidates.json` and chosen by reading its title; the file
also carries, for each, the sentence-level reason it is cited, because a reference list whose
entries have no role in the argument is padding.

Usage: python3 recent.py     (rewrites selection.json with the arXiv entries merged in)
"""

from __future__ import annotations

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

# arXiv id -> (citation key, the role the citation plays)
RECENT = {
    "2609.32877": ("multilanglogics", "multi-language program logics"),
    "2609.39678": ("aletheia", "permission-minimality testing for coding-agent rules"),
    "2609.38499": ("mallocsan", "a memory-safety tool for closed-source applications"),
    "2609.37849": ("manualopt", "whether manual software optimisation is still worthwhile"),
    "2609.36279": ("nominalproofs", "shallow embeddings and proofs without nominals"),
    "2609.34922": ("cfsmcompose", "safe composition of communicating systems"),
    "2609.34894": ("heytingml", "algebraic semantics for a matching logic"),
    "2609.34892": ("matchedcomposition", "dependently typed model composition"),
    "2609.34927": ("sessionlattices", "session-type state spaces as lattices"),
    "2609.39783": ("compasspatches", "predicting relationships among vulnerability patches"),
    "2609.38402": ("culpritsearch", "reducing a bug search space with semantic retrieval"),
    "2609.37726": ("mcrl2coordination", "modelling shared-space coordination in mCRL2"),
    "2609.40119": ("assurancecases", "machine-checked assurance cases generated from a codebase"),
    "2609.39022": ("verifguidance", "verification failures turned into reusable guidance"),
    "2609.38981": ("vosti", "specifying, implementing and verifying a deterministic inference pipeline"),
    "2609.35425": ("prefixoracles", "semantic prefix oracles and differential validation"),
    "2609.34886": ("verusskill", "reusable skill for LLM-assisted Verus verification"),
    "2609.33813": ("refinedstream", "a stream protocol designed by formal refinement"),
    "2609.39568": ("selfspec", "self-specifying verifiable code generation"),
    "2609.39086": ("errhealing", "benchmark and guarantees for runtime error healing"),
    "2609.37985": ("mergednotmeasured", "empirical study of performance fixes merged without measurement"),
    "2609.37322": ("mubric", "mutation testing used to guide rubric generation"),
    "2609.37315": ("contractaudit", "executable-contract audit of tool-using agents"),
    "2609.37294": ("safellmse", "statistical evaluation and reporting for LLM-based SE"),
    "2609.38237": ("trustledger", "execution check for C-to-Lean autoformalization"),
    "2609.34883": ("dafnymodels", "two computational models formalized in Dafny"),
    "2609.34882": ("omegatest", "the Omega test formalized in Dafny"),
    "2609.38492": ("leangroups", "machine-checked computational group theory in Lean 4"),
    "2609.36065": ("quantumequiv", "equivalence checking of hybrid quantum programs"),
    "2609.34089": ("faultless", "a program-equivalence technique for validating decompilation"),
    "2609.30254": ("forte", "a sensitivity type system for imperative Rust"),
    "2609.30062": ("oxidize", "structure-preserving C-to-Rust translation"),
    "2609.34646": ("c11semantics", "operational semantics for C11 programs"),
    "2609.25335": ("gradertl", "evaluating generated RTL beyond compilation"),
    "2609.39009": ("tristate", "a tristate multiplier formalized in Rocq"),
    "2609.34889": ("patiencesort", "certification of a sorting algorithm in two provers"),
    "2609.37728": ("perfmodels", "formal reasoning about performance models"),
    "2609.34069": ("certporting", "certificate-driven software porting"),
}


# An entry whose identifier cannot be resolved is DELETED, not left in place: the journal's
# rule is "never submit an unverifiable citation", and an entry that is merely unreachable at the
# moment of checking is exactly that.  Removing one recent work costs the paper nothing.
DROPPED = {
    "2609.34922": "arXiv returned HTTP 429 on every lookup within this round; unverifiable, so not cited",
    "2609.34894": "arXiv returned HTTP 429 on every lookup within this round; unverifiable, so not cited",
    "2609.38499": "arXiv returned HTTP 429 on every lookup within this round; unverifiable, so not cited",
    "2609.34886": "arXiv returned HTTP 429 on every lookup within this round; unverifiable, so not cited",
}


def main() -> int:
    cpath = os.path.join(HERE, "candidates.json")
    spath = os.path.join(HERE, "selection.json")
    cands = {c["id"].split("v")[0]: c for c in json.load(open(cpath)) if c["src"] == "arxiv"}
    sel = json.load(open(spath))

    added, missing = [], []
    have = {a["key"] for a in sel["accepted"]}
    for aid, (key, role) in sorted(RECENT.items()):
        if key in have or aid in DROPPED:
            continue
        c = cands.get(aid)
        if c is None:
            missing.append(aid)
            continue
        sel["accepted"].append({
            "key": key, "title": c["title"], "year": c["year"], "venue": "arXiv preprint",
            "doi": "", "arxiv": aid, "authors": [{"family": a, "given": ""}
                                                 for a in c["authors"]],
            "source": "arxiv", "match_score": 1.0, "query": f"harvested by topic, id {aid}",
            "difference": "",
            "role": role,
        })
        added.append(key)

    with open(spath, "w") as fh:
        json.dump(sel, fh, indent=1)
    print(f"added {len(added)} recent arXiv entries; selection now {len(sel['accepted'])}")
    for k in added:
        print(f"  {k}")
    if missing:
        print(f"  ids not found in the harvest: {missing}")
    for aid, why in DROPPED.items():
        print(f"  dropped (unverifiable): {aid} -- {why}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
