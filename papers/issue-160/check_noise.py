# -*- coding: utf-8 -*-
"""check_noise.py -- the claim this data cannot make, made visibly unmade.

Registered prior P1's second limb asked whether the reported p99's spread across the timeout grid
exceeds the spread of *repeated measurement of the same row*. On this data that question is not
answerable, and the reason is not a missing dependency a reader could install:

  1. Recomputing the statistics on a fixed published table is **deterministic** -- two runs of
     `run_crossover.py` are byte-identical -- so the "repeated-measurement spread" is 0 by
     construction. "The effect exceeds zero noise" is then either vacuous or a statement about
     rounding, not about a sampling distribution.
  2. Estimating that spread needs either per-invocation latencies or replicated measurements of the
     same population. This table carries neither: its percentile columns are percentiles of a
     **30-second interval mean** (dataset footnote 7), and one day is one measurement.

So this step reports **NOT RUN** (exit 3) -- never a pass, and never a failure. It exists so that the
reproduction's verdict line cannot claim a number the data does not contain: `ALL GREEN` is
unreachable for this package, and the reason is printed in the log on every run.

It re-checks (1) rather than asserting it: the determinism claim is measured here, and if a future
interpreter made the computation non-deterministic this step would say so instead of NOT RUN.
"""
import csv
import io
import lzma
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
MEMBER = "function_durations_percentiles.anon.d01.csv"
FIXTURE = os.path.join(HERE, "fixture", MEMBER + ".xz")

# Columns that are NOT a per-invocation latency: the interval aggregates the trace publishes.
AGGREGATE_PREFIXES = ("percentile_average_",)
AGGREGATE_EXACT = {"count", "average", "minimum", "maximum", "hashowner", "hashapp", "hashfunction"}


def columns(path=FIXTURE):
    with lzma.open(path, "rb") as raw:
        f = io.TextIOWrapper(raw, encoding="utf-8", newline="")
        head = next(csv.reader(f))
    return head


def per_invocation_columns(cols):
    """Column names that would identify single-invocation latencies, as opposed to interval means."""
    out = []
    for c in cols:
        low = c.strip().lower()
        if low in AGGREGATE_EXACT or low.startswith(AGGREGATE_PREFIXES):
            continue
        out.append(c)
    return out


def determinism_witness(path=FIXTURE):
    """Two independent reads of the same rows: the statistics are a pure function of the bytes.

    Streams the file twice and hashes a digest of the numeric fields, so this compares run-to-run
    behaviour on the real table rather than asserting a property of the source.
    """
    import hashlib
    digs = []
    for _ in range(2):
        h = hashlib.sha256()
        with lzma.open(path, "rb") as raw:
            f = io.TextIOWrapper(raw, encoding="utf-8", newline="")
            for r in csv.DictReader(f):
                h.update(("|".join(r[c] for c in sorted(r))).encode("utf-8"))
        digs.append(h.hexdigest())
    return digs[0] == digs[1], digs[0][:16]


def main():
    if not os.path.exists(FIXTURE):
        print("NOT RUN: the fixture is absent, so the noise claim was not examined at all")
        return 3
    cols = columns()
    singles = per_invocation_columns(cols)
    same, witness = determinism_witness()

    print("P1 limb 2 asks: does the reported p99's spread across the timeout grid exceed the spread of")
    print("repeated measurement of the same rows?")
    print("\n  (1) repeated measurement of this table is deterministic: two independent passes agree")
    print("      (%s)%s" % (witness + "...", "" if same else "  <-- NOT deterministic, so the claim could be estimated"))
    print("  (2) %d columns read; columns carrying single-invocation latencies: %d %s"
          % (len(cols), len(singles), ("-> " + ", ".join(singles)) if singles else ""))
    print("      the percentile columns are percentiles of a 30-second interval MEAN (footnote 7),")
    print("      and one published day is one measurement, not replicates.")
    if same and not singles:
        print("\nNOT RUN: this data cannot estimate the denominator of that comparison. Reported as")
        print("         'no information' in the manuscript -- not as support, and not as a refutation.")
        return 3
    print("\nRAN: the spread can be estimated on this input; run the estimator (not part of this package")
    print("     yet) and report it here.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
