# -*- coding: utf-8 -*-
"""run_crossover.py -- the day-01 measurement behind issue #160.

Reads the trace's day-01 duration table from the committed fixture, reconstructs each row's
interval-mean quantile ladder, and reports three things:

  A. THE SAMPLE-COUNT LIMIT (the headline, and the only one not derivable from censoring arithmetic)
     For each row: how many observations sit above the 99th percentile, and whether the row can
     resolve it at all. Reported per row, aggregated here.

  B. THE CROSSOVER AT A PRE-DECLARED TIMEOUT GRID
     `T = k * median` for k in {2, 4, 8, 16, 32} -- a configuration style, NOT a quantile of the
     number under test. For each k: the empirical distribution of the censored fraction `c`, the
     fraction of rows whose true quantile the harness can no longer identify (`c > 1-q`), and how far
     the printed number sits below the truth on those rows.

     The grid was fixed in the issue thread before this program was run, and it is a constant here.
     Evaluating the crossover at `T = p99` would make `c = 1-q` by construction -- an identity in a
     measurement's clothes -- so that point is deliberately absent from the grid.

  C. THE COST LAW ON REAL RANGES
     `R = p100/p50` per row (both knots are percentiles of the SAME quantity, the interval mean), and
     `K = ceil(log R / log(1+eps))` -- a lower bound on the invocation-level cost, because the
     interval mean is smoother than the invocations it averages.

Controls, run every time:
  * NO CENSORING -- T above the row's maximum: the quantile is identified and the printed number
    equals the truth. If this ever stops holding, the instrument is broken, not the data.
  * FLAT WORKLOAD -- rows with R = 1: the cost law must return exactly one level.

INPUT. The trace member `function_durations_percentiles.anon.d01.csv` (12,156,002 B, sha256 pinned in
`fixture/MEMBER_SHA256`), committed xz-compressed because the upstream release is a 143 MB archive and
a reviewer must not have to fetch 143 MB to check a number. The digest is recorded in the artefact, so
the output states which bytes it came from. `TRACE_CSV` overrides the input for a reader who has the
full archive and wants another day -- the numbers below are this member's.

Outputs `results/crossover.json`. Every number the paper states comes from that file.
"""
import csv
import io
import json
import lzma
import os
import sys

import censored_tail as ct

HERE = os.path.dirname(os.path.abspath(__file__))
MEMBER = "function_durations_percentiles.anon.d01.csv"
FIXTURE = os.path.join(HERE, "fixture", MEMBER + ".xz")
OUT = os.path.join(HERE, "results", "crossover.json")

Q = 0.99
KGRID = (2, 4, 8, 16, 32)          # fixed in the issue thread before this run
EPS = (0.05, 0.10, 0.20)
SRC = os.environ.get("TRACE_CSV", FIXTURE)


def pctl(xs, p):
    """Linear-interpolation percentile of a plain list. Deterministic; no library dependency."""
    if not xs:
        return None
    s = sorted(xs)
    if len(s) == 1:
        return s[0]
    pos = p * (len(s) - 1)
    lo = int(pos)
    hi = min(lo + 1, len(s) - 1)
    return s[lo] + (s[hi] - s[lo]) * (pos - lo)


def open_source(path):
    """Open the trace table as text, decompressing when the input is the committed .xz.

    A reader who points `TRACE_CSV` at an extracted CSV gets the same program; `.xz` is a property
    of how this package stores its input, not of the measurement.
    """
    if path.endswith(".xz"):
        raw = lzma.open(path, "rb")
        text = io.TextIOWrapper(raw, encoding="utf-8", newline="")
    else:
        text = open(path, newline="", encoding="utf-8")
    return text


def digest_of(path):
    """sha256 of the *decompressed* bytes -- the identity of the data, not of its storage."""
    import hashlib
    h = hashlib.sha256()
    if path.endswith(".xz"):
        with lzma.open(path, "rb") as f:
            for chunk in iter(lambda: f.read(1 << 20), b""):
                h.update(chunk)
    else:
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(1 << 20), b""):
                h.update(chunk)
    return h.hexdigest()


def main():
    rows = 0
    refused = {"crossing_ladder": 0, "zero_median": 0, "unparseable": 0}
    kept = []

    src_digest = digest_of(SRC)
    f = open_source(SRC)
    try:
        for r in csv.DictReader(f):
            rows += 1
            pts = ct.ladder_points(r)
            if pts is None:
                # distinguish the two refusals so the count says WHY, not just "bad"
                try:
                    vals = [float(r[c]) for _, c in ct.LADDER]
                    if any(b < a for a, b in zip(vals, vals[1:])):
                        refused["crossing_ladder"] += 1
                    elif vals[3] <= 0:
                        refused["zero_median"] += 1
                    else:
                        refused["unparseable"] += 1
                except Exception:
                    refused["unparseable"] += 1
                continue
            try:
                count = int(r["Count"])
            except Exception:
                continue
            kept.append(dict(pts=pts, count=count, n_obs=ct.observations_above(count, Q),
                             R=ct.quantile(pts, 1.0) / ct.quantile(pts, 0.5)))
    finally:
        f.close()

    # ---- A. the sample-count limit ---------------------------------------------------------
    resolvable = [k for k in kept if ct.resolvable(k["count"], Q)]
    count_limit = dict(
        q=Q, rows=rows, usable=len(kept), refused=refused,
        resolvable=len(resolvable),
        resolvable_frac=round(len(resolvable) / float(len(kept)), 4),
        unresolvable_frac=round(1.0 - len(resolvable) / float(len(kept)), 4),
        below_100=sum(1 for k in kept if k["count"] < 100),
        below_1000=sum(1 for k in kept if k["count"] < 1000),
        below_100_frac=round(sum(1 for k in kept if k["count"] < 100) / float(len(kept)), 4),
        below_1000_frac=round(sum(1 for k in kept if k["count"] < 1000) / float(len(kept)), 4),
        n_obs_median=round(pctl([k["n_obs"] for k in kept], 0.5), 4),
        unit="interval mean (30-s average), NOT single invocations -- trace footnote 7",
    )

    # ---- B. the crossover on the pre-declared grid -----------------------------------------
    cells = []
    for k_ in KGRID:
        cs, binds, short = [], 0, []
        for row in kept:
            med = ct.quantile(row["pts"], 0.5)
            T = k_ * med
            c = ct.censored_fraction(row["pts"], T)
            cs.append(c)
            if not ct.identified(Q, c):
                binds += 1
                # ONLY the binding rows are interesting. On an identified row the printed number
                # equals the truth whenever the timeout sits above the row's top knot, so a
                # ratio over all identified rows is a column of 1.0000 that says nothing. What
                # the reader needs is: on the rows where the harness CANNOT identify the
                # quantile, how far below the truth does it print?
                rep, lo, hi = ct.identified_set(row["pts"], Q, T)
                true = ct.quantile(row["pts"], Q)
                if rep > 0:
                    short.append(true / rep)
        cells.append(dict(k=k_, T_rule="k * row median", rows=len(kept),
                          binds=binds, binds_frac=round(binds / float(len(kept)), 4),
                          c_median=round(pctl(cs, 0.5), 6), c_p10=round(pctl(cs, 0.1), 6),
                          c_p90=round(pctl(cs, 0.9), 6), c_max=round(max(cs), 6),
                          identified_frac=round(1.0 - binds / float(len(kept)), 4),
                          # true/printed ON THE BINDING ROWS: how much the harness understates
                          understated_by_median=round(pctl(short, 0.5), 4) if short else None,
                          understated_by_p90=round(pctl(short, 0.9), 4) if short else None,
                          understated_by_max=round(max(short), 4) if short else None))

    # ---- C. the cost law on real ranges ----------------------------------------------------
    Rs = [k["R"] for k in kept]
    cost = dict(rule="K = ceil(log R / log(1+eps)), R = p100/p50 (same-space, interval means)",
                R_median=round(pctl(Rs, 0.5), 4), R_p90=round(pctl(Rs, 0.9), 4),
                R_max=round(max(Rs), 4), R_min=round(min(Rs), 4))
    for eps in EPS:
        ks = [ct.levels_needed(R, eps) for R in Rs]
        cost["K_at_%d" % int(eps * 100)] = dict(median=int(pctl(ks, 0.5)), p90=int(pctl(ks, 0.9)),
                                                max=int(max(ks)),
                                                frac_at_one=round(sum(1 for x in ks if x == 1) / float(len(ks)), 4))

    # ---- controls --------------------------------------------------------------------------
    # no censoring: timeout above the row's own maximum
    exact = []
    for row in kept[:5000]:
        T = ct.quantile(row["pts"], 1.0) * 1.0001
        rep, lo, hi = ct.identified_set(row["pts"], Q, T)
        exact.append(hi == lo and abs(rep - lo) <= 1e-9 * max(1.0, lo))
    # Two different sets, two different names. `levels_needed(R, eps) == 1` holds for `R <= 1+eps`,
    # not for `R == 1`: at eps=5% that is 12,664 rows, while only 11,972 rows have `p100 == p50`
    # exactly. A single key called `flat_rows` holding the first while its note described the second
    # was a label that lied about its own number (found 2026-10-31 while writing the manuscript).
    controls = dict(
        no_censoring_rows=len(exact),
        no_censoring_identified_and_exact_frac=round(sum(exact) / float(len(exact)), 6),
        flat_rows_R_eq_1=sum(1 for k in kept if k["R"] == 1.0),
        flat_rows_R_eq_1_frac=round(sum(1 for k in kept if k["R"] == 1.0) / float(len(kept)), 4),
        rows_needing_one_level_at_eps_5=sum(1 for k in kept if ct.levels_needed(k["R"], 0.05) == 1),
        note=("flat_rows_R_eq_1 counts rows whose ladder has no range at all (p100 == p50); "
              "rows_needing_one_level_at_eps_5 counts rows the cost law certifies with a single "
              "level, which is R <= 1.05 and is the larger set. A timeout above the maximum prints "
              "the truth, which is what the no-censoring control checks."),
    )

    # The input's identity travels with the numbers: a reader must be able to see which bytes these
    # came from without trusting a README. Relative paths only -- an absolute path would make the
    # artefact a property of the machine that built it.
    out = dict(q=Q, source=MEMBER, kgrid=list(KGRID), eps=list(EPS),
               input=dict(member=MEMBER,
                          interval_seconds=30,
                          interval_note=("the trace aggregates every 30 seconds and publishes "
                                         "percentiles of the per-interval MEAN (dataset footnote 7); "
                                         "this is the unit of every range in this artefact"),
                          fixture=os.path.relpath(SRC, HERE) if os.environ.get("TRACE_CSV") is None
                          else "TRACE_CSV override: " + os.path.basename(SRC),
                          sha256_of_decompressed_bytes=src_digest),
               count_limit=count_limit, cells=cells, cost=cost, controls=controls)
    json.dump(out, open(OUT, "w"), indent=1, sort_keys=True)

    # ---- what the run prints ---------------------------------------------------------------
    print("input: %s  sha256(decoded)=%s" % (os.path.basename(SRC), src_digest[:16] + "..."))
    print("rows read: %d | usable ladders: %d | refused: %s" % (rows, len(kept), refused))
    print("\nA. sample-count limit (q=%.2f, unit = interval mean)" % Q)
    print("   resolvable (expects >=1 observation above p99): %d / %d = %.1f%%"
          % (count_limit["resolvable"], len(kept), 100 * count_limit["resolvable_frac"]))
    print("   NOT resolvable: %.1f%%   (Count<100: %.1f%%   Count<1000: %.1f%%)"
          % (100 * count_limit["unresolvable_frac"], 100 * count_limit["below_100_frac"],
             100 * count_limit["below_1000_frac"]))
    print("\nB. crossover at the pre-declared grid (T = k * median)")
    print("   %4s %10s %10s %10s %14s %10s"
          % ("k", "binds %", "c median", "c p90", "understated x", "p90 x"))
    for c_ in cells:
        print("   %4d %10.2f %10.4f %10.4f %14s %10s"
              % (c_["k"], 100 * c_["binds_frac"], c_["c_median"], c_["c_p90"],
                 "%.2f" % c_["understated_by_median"] if c_["understated_by_median"] is not None else "-",
                 "%.2f" % c_["understated_by_p90"] if c_["understated_by_p90"] is not None else "-"))
    print("   ('understated x' = true p99 / printed p99, taken ONLY on rows where the boundary binds)")
    print("\nC. cost law over real ranges")
    print("   R = p100/p50: median %.2f  p90 %.1f  max %.1f" % (cost["R_median"], cost["R_p90"], cost["R_max"]))
    for eps in EPS:
        d = cost["K_at_%d" % int(eps * 100)]
        print("   eps=%2.0f%%  K median %4d  p90 %4d  (rows needing exactly 1 level: %.1f%%)"
              % (eps * 100, d["median"], d["p90"], 100 * d["frac_at_one"]))
    print("\ncontrols: no-censoring exact on %d/%d rows (%.6f)"
          % (sum(exact), len(exact), controls["no_censoring_identified_and_exact_frac"]))
    print("          flat rows (R == 1): %d (%.2f%%) | rows needing one level at eps=5%%: %d (%.2f%%)"
          % (controls["flat_rows_R_eq_1"], 100 * controls["flat_rows_R_eq_1_frac"],
             controls["rows_needing_one_level_at_eps_5"],
             100 * controls["rows_needing_one_level_at_eps_5"] / float(len(kept))))
    if controls["no_censoring_identified_and_exact_frac"] < 1.0:
        print("CONTROL FAILED: a timeout above the maximum must identify the quantile exactly")
        return 1
    print("\n-> %s" % os.path.relpath(OUT, HERE))
    return 0


if __name__ == "__main__":
    sys.exit(main())
