#!/usr/bin/env python3
"""check_claims.py -- read the artefact back and test the claims the paper makes about it.

A paper's sentences are claims about numbers, and a number that no program re-checks will drift
away from the sentence that describes it. This program is that check: it reads
`results/mechanism.json` and asserts, mechanically, the statements the manuscript will carry. If a
claim stops holding -- because a cell changed, or because a run was made on a different corpus --
this exits 1 and the reproduction fails.

Two of the checks are the instrument's endpoint controls, and they are the reason the table means
anything: an instrument that cannot return "fully identified" on input where the answer is known,
and cannot return "maximally unidentified" on constructed input, has not been shown to measure
either, and any number it produces elsewhere is uninterpreted.

Reads : results/mechanism.json
Exit  : 0 all claims hold; 1 a claim does not hold or the artefact is missing.
"""
import json
import sys

FAILED = 0


def check(name, ok, detail=""):
    global FAILED
    print("  [%s] %s%s" % ("ok" if ok else "FAIL", name, (" -- " + detail) if detail else ""))
    if not ok:
        FAILED += 1


def main():
    try:
        d = json.load(open("results/mechanism.json"))
    except FileNotFoundError:
        print("  [FAIL] results/mechanism.json is missing -- run run_mechanism.py first")
        return 1

    cells = d["cells"]
    by = {c["tag"]: c for c in cells}
    corpus = d["corpus"]
    n = corpus["n"]
    fams = [c for c in cells if c["tag"].split("/")[0] in ("Hamming", "PQ", "SQ")]

    print("claims about results/mechanism.json (%d x %d corpus, %d queries, k=%d)"
          % (n, corpus["d"], corpus["n_queries"], corpus["k"]))

    # ---- endpoint control 1: identified where the answer is known -------------------------
    fl = by["float/raw descriptors"]
    check("float endpoint is fully identified (median boundary tie group == 1)",
          fl["median_t"] == 1, "median_t=%s" % fl["median_t"])
    check("float endpoint floor == 1.0000", fl["mean_floor"] == 1.0, "mean_floor=%s" % fl["mean_floor"])

    # ---- endpoint control 2: maximally unidentified on constructed input ------------------
    cn = by["constructed/all points identical"]
    check("constructed endpoint puts every point in one tie group",
          cn["median_t"] >= n - 1, "median_t=%s of n=%d" % (cn["median_t"], n))
    check("constructed endpoint floor == 0.0000", cn["mean_floor"] == 0.0, "mean_floor=%s" % cn["mean_floor"])

    # ---- the axis ------------------------------------------------------------------------
    check("the axis orders the table (log-log Pearson < -0.9)",
          d["log_log_pearson"] < -0.9, "r=%.4f over %d cells" % (d["log_log_pearson"], len(fams)))
    coarsest = min(fams, key=lambda c: c["median_atoms"])
    finest = max(fams, key=lambda c: c["median_atoms"])
    check("the coarsest cell has the largest tie group",
          coarsest["median_t"] >= finest["median_t"],
          "%s t=%s vs %s t=%s" % (coarsest["tag"], coarsest["median_t"],
                                  finest["tag"], finest["median_t"]))

    # ---- the count is stated, and stated as what it is ------------------------------------
    configs = {tuple(c["tag"].split("/")[:2]) for c in fams}
    check("every family cell declares its query count",
          all(c["n_queries"] == corpus["n_queries"] for c in fams))
    print("  [info] %d seed-level cells over %d distinct (family, budget) configurations"
          % (len(fams), len(configs)))
    print("  [info] seeds are not independent confirmations: the cell count is the seed count, "
          "the configuration count is the evidence count")

    print("CLAIMS: %s" % ("PASS" if FAILED == 0 else "%d FAILED" % FAILED))
    return 0 if FAILED == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
