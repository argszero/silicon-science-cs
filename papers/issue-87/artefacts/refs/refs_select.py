#!/usr/bin/env python3
"""#87 R403 -- select the reference candidates from the harvest, bucketed by the claim they will carry.

Deterministic: no network, reads refs_raw.json, prints a compact listing grouped by topical bucket so the
author can choose (and write one true difference line per chosen work).  The buckets exist because a
bibliography is a set of *citations*, so the selection must be driven by the claims the paper makes, not
by what the index happened to return.

Buckets (a work may match several; it is listed once, under its highest-scoring bucket):
  A  quantum kernel methods / theory of the quantum kernel
  B  quantum feature maps, embeddings, geometry, entanglement metrics
  C  benchmarks and audits of the quantum advantage contract
  D  trainability: barren plateaus, kernel concentration, collapse
  E  classical kernel methodology: alignment, selection, multiple kernels, approximations
  F  statistical methodology: resampling, multiple testing, model selection, comparison protocols
  G  quantum computation, simulation and classical simulability
  H  learning theory, capacity and generalisation
"""
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "refs_raw.json")

BUCKETS = {
    "A": dict(name="quantum kernel methods / theory",
              kw=["quantum kernel", "kernel method", "kernel ridge", "fidelity kernel", "quantum svm",
                  "support vector machine", "quantum advantage", "kernel-based"]),
    "B": dict(name="feature maps, embeddings, geometry",
              kw=["feature map", "embedding", "entanglement", "geometry", "kernel matrix", "data encoding",
                  "encoding", "metric", "manifold"]),
    "C": dict(name="benchmarks and audits of the advantage",
              kw=["benchmark", "audit", "reproduc", "fair comparison", "baseline", "empirical study",
                  "systematic evaluation", "meta-analysis"]),
    "D": dict(name="trainability, plateaus, collapse",
              kw=["barren plateau", "trainab", "concentration", "vanishing gradient", "expressivity",
                  "collapse", "generalization", "generalisation"]),
    "E": dict(name="classical kernel methodology",
              kw=["kernel alignment", "kernel target alignment", "multiple kernel", "random feature",
                  "nystrom", "kernel selection", "hyperparameter", "bandwidth", "regulariz", "regularis",
                  "kernel approximation", "gaussian process"]),
    "F": dict(name="statistical methodology",
              kw=["multiple testing", "false discovery", "resampl", "bootstrap", "cross-validation",
                  "cross validation", "statistical significance", "confidence interval", "power analysis",
                  "paired test"]),
    "G": dict(name="quantum computation, simulation, simulability",
              kw=["statevector", "simulat", "classical simul", "dequant", "quantum circuit", "nqubit",
                  "qubit", "clifford", "tensor network"]),
    "H": dict(name="learning theory, capacity, generalisation",
              kw=["generalization bound", "generalisation bound", "capacity", "reproducing kernel",
                  "universal kernel", "overfit", "sample complexity", "no free lunch", "pac"]),
}
ORDER = ["A", "B", "C", "D", "E", "F", "G", "H"]


def score(text, kws):
    t = text.lower()
    return sum(t.count(k) for k in kws)


def main():
    raw = json.loads(io.open(RAW, encoding="utf-8").read())
    seen = {}
    for lab, blk in raw["arxiv"].items():
        for r in blk["rows"]:
            if r["id"] not in seen:
                seen[r["id"]] = r
    rows = []
    for r in seen.values():
        text = (r["title"] + " " + r["summary"]).lower()
        scores = {b: score(text, BUCKETS[b]["kw"]) for b in ORDER}
        best = max(ORDER, key=lambda b: (scores[b], -ORDER.index(b)))
        r["bucket"] = best
        r["scores"] = scores
        r["total"] = sum(scores.values())
        rows.append(r)
    rows.sort(key=lambda r: (-r["scores"][r["bucket"]], -r["total"], r["id"]))
    take = int(sys.argv[1]) if len(sys.argv) > 1 else 22
    for b in ORDER:
        blk = [r for r in rows if r["bucket"] == b][:take]
        print("\n=== %s  %s  (%d shown of %d) ==="
              % (b, BUCKETS[b]["name"], len(blk), sum(1 for r in rows if r["bucket"] == b)))
        for r in blk:
            a = r["authors"][0].split()[-1] if r["authors"] else "?"
            print("  %-11s %s %-13s %s" % (r["id"], r["year"], a[:13],
                                           r["title"][:96]))
    print("\n=== CROSSREF (32 records, all read per DOI) ===")
    for doi, r in sorted(raw["crossref"].items()):
        a = (r["authors"][0] if r["authors"] else "?")
        print("  %-38s %s %-16s %s" % (doi, r["year"], a[:16], r["title"][:70]))
    print("\ntotal arxiv within buckets: %d" % len(rows))


if __name__ == "__main__":
    sys.exit(main())
