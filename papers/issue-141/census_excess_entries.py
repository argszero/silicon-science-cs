#!/usr/bin/env python3
"""issue #141 -- R655: the naive transport law, re-read at the UNIT THE STATISTIC LIVES ON.

WHY THIS EXISTS.  The v4 certificate states the naive law at the PROTOCOL level and reports its
violator set as the single constructed witness `rank_score`.  The transport statistic, however, is
defined on an ENTRY (a game, a protocol, and a PAIR of populations): `excess` is a pair-level object
while `faithful` is a cell-level one.  A reader who re-reads the naive law at that unit -- which is
the unit every transport number in the paper is quoted at -- gets a different verdict.  This script
takes that reading, and it takes it with the denominator repaired:

    the two populations of an entry may rank the payoff IDENTICALLY (base == 0).  There the payoff
    ordering itself incurs no loss, so a design that reads neither the payoff nor the population has
    excess == 0 by arithmetic rather than by faithfulness.  285 of the 1,026 entries are of that
    kind, and a count taken over the full domain is a count over them.  Every count here is therefore
    reported TWICE: over the full domain, and over the entries where transport has something to
    detect (base > 0).

WHAT IT COMPUTES (all from v4's single memoised scan -- no new instrument, no new grid):
  1. the domain and its degeneracy    (entries, base == 0 / base > 0)
  2. the FORWARD leg                  (faithful in both populations => excess == 0)   a theorem
  3. the NAIVE law at entry level     (excess == 0 <=> faithful), full domain and base > 0,
                                      with the violators attributed to record vs added designs
  4. the EVALUATED set of record      (the entries C6c restricts its converse reading to) and the
                                      fact that it is DISJOINT from 3's record violators, though
                                      `|evaluated over all protocols| == |record violators|` -- a
                                      coincidence of counts over two different sets
  5. the structural witness re-read   (a population-blind design has T_raw == 0 in every entry; its
                                      T_EXCESS is 0 only where base == 0)

CEREMONY.  `--out` writes the artefact; the report is printed always.  The forward leg and the
degeneracy split each carry a plant that makes them fire, so "0" here is a reading and not an
absence of machinery (Class 206c).  Deterministic: no seeds, no sampling, sorted output.

Author: how2how2how2-arch
"""
import argparse
import hashlib
import json
import os
import sys
from collections import Counter, OrderedDict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import spike_v4 as V4  # noqa: E402  the instrument of record


# ------------------------------------------------------------------------------------------------
# the readings

def parts(k):
    g, p, pair = k.split("|")
    p1, p2 = pair.split(">")
    return g, p, p1, p2


def z(s):
    """A Fraction is serialised as a string; zero must be read, never assumed."""
    return str(s) in ("0", "0/1")


def build():
    SC = V4.scan()
    cells, tr = SC["cells"], SC["tr"]
    prot = V4.PROTOCOLS
    added = {V4.WITNESS, V4.CONSTRUCTED_WITNESS}
    record = [p for p in prot if p not in added]

    def cell(g, p, pop):
        return cells["%s|%s|%s" % (g, pop, p)]

    def faithful(g, p, pop):
        return str(cell(g, p, pop)["tau"]) == "1"

    ori = V4.orientations(cells, prot)

    def deterministic(g, p, pop):
        """The orientation predicate C6c reads: +-payoff (tau in {+1,-1}), not merely faithful."""
        return ori["%s|%s|%s" % (g, pop, p)] != 0

    d = {"entries": len(tr), "protocols": len(prot), "record_protocols": len(record)}

    # (1) the domain and its degeneracy
    deg = [k for k, v in tr.items() if z(v["base"])]
    d["base_zero"] = len(deg)
    d["base_positive"] = len(tr) - len(deg)
    d["base_values"] = OrderedDict(sorted(Counter(str(v["base"]) for v in tr.values()).items()))
    d["base_positive_and_excess_zero"] = sum(
        1 for k, v in tr.items() if not z(v["base"]) and z(v["excess"]))

    # (2) the FORWARD leg -- faithful in BOTH populations => excess == 0 (a theorem)
    fwd_bad_all, fwd_bad_pos = [], []
    for k, v in tr.items():
        g, p, p1, p2 = parts(k)
        if faithful(g, p, p1) and faithful(g, p, p2) and not z(v["excess"]):
            fwd_bad_all.append(k)
            if not z(v["base"]):
                fwd_bad_pos.append(k)
    d["forward_counterexamples_all"] = len(fwd_bad_all)
    d["forward_counterexamples_base_positive"] = len(fwd_bad_pos)

    # (3) the NAIVE law at entry level: excess == 0  <=>  faithful in both populations
    def violators(restrict_pos):
        out = []
        for k, v in tr.items():
            if not z(v["excess"]):
                continue
            if restrict_pos and z(v["base"]):
                continue
            g, p, p1, p2 = parts(k)
            if faithful(g, p, p1) and faithful(g, p, p2):
                continue
            out.append(k)
        return out

    for label, pos in (("all", False), ("base_positive", True)):
        V = violators(pos)
        VR = [k for k in V if k.split("|")[1] in record]
        d["violators_" + label] = len(V)
        d["violators_record_" + label] = len(VR)
        d["violators_record_%s_by_protocol" % label] = OrderedDict(
            sorted(Counter(k.split("|")[1] for k in VR).items()))
        d["violators_record_%s_designs" % label] = len({k.split("|")[1] for k in VR})

    # (4) the evaluated set C6c reads, and its disjointness from (3)'s record violators
    ev_all = [k for k in tr
              if deterministic(parts(k)[0], parts(k)[1], parts(k)[2]) and deterministic(parts(k)[0], parts(k)[1], parts(k)[3])]
    ev_rec = [k for k in ev_all if k.split("|")[1] in record]
    recv = [k for k in violators(False) if k.split("|")[1] in record]
    inter = set(ev_rec) & set(recv)
    d["evaluated_all"] = len(ev_all)
    d["evaluated_record"] = len(ev_rec)
    d["evaluated_record_by_protocol"] = OrderedDict(
        sorted(Counter(k.split("|")[1] for k in ev_rec).items()))
    d["evaluated_record_intersect_record_violators"] = len(inter)
    d["count_coincidence"] = (len(ev_all) == len(recv))

    # (5) the structural witness, re-read: T_raw vs T_excess
    for pr in (V4.FRAGILE_REFERENCE, V4.WITNESS, V4.CONSTRUCTED_WITNESS):
        ks = [k for k, v in tr.items() if k.split("|")[1] == pr]
        d["%s_raw_zero" % pr] = sum(1 for k in ks if z(tr[k]["raw"]))
        d["%s_excess_zero" % pr] = sum(1 for k in ks if z(tr[k]["excess"]))
        d["%s_excess_zero_base_positive" % pr] = sum(
            1 for k in ks if z(tr[k]["excess"]) and not z(tr[k]["base"]))
        d["%s_entries" % pr] = len(ks)

    d["_scan"] = {"cells": len(cells), "transport": len(tr)}
    d["_certificate"] = certificate(cells, tr, prot, record, cell, faithful, ori)
    return d, cells, tr, prot, record, cell, faithful, ori


# ------------------------------------------------------------------------------------------------
# the certificate: every "0" here must be able to become a non-zero

def certificate(cells, tr, prot, record, cell, faithful, ori):
    ok = total = 0
    log = []

    def check(name, cond, detail=""):
        nonlocal ok, total
        total += 1
        if cond:
            ok += 1
            log.append("  OK   " + name)
        else:
            log.append("  FAIL " + name + ("  [" + detail + "]" if detail else ""))

    # C1 the forward leg is a theorem and holds over the whole domain
    bad = [k for k, v in tr.items()
           if faithful(parts(k)[0], parts(k)[1], parts(k)[2]) and faithful(parts(k)[0], parts(k)[1], parts(k)[3])
           and not z(v["excess"])]
    check("forward leg: faithful in both populations => excess == 0, over all %d entries" % len(tr),
          not bad, "counterexamples: %s" % bad[:3])

    # C1-PLANT: corrupt one faithful entry's excess and watch the leg fire
    ka = next(k for k, v in tr.items()
              if faithful(parts(k)[0], parts(k)[1], parts(k)[2]) and faithful(parts(k)[0], parts(k)[1], parts(k)[3]))
    planted = dict(tr)
    planted[ka] = dict(planted[ka], excess="1/14")
    bad_p = [k for k, v in planted.items()
             if faithful(parts(k)[0], parts(k)[1], parts(k)[2]) and faithful(parts(k)[0], parts(k)[1], parts(k)[3])
             and not z(v["excess"])]
    check("C1-PLANT corrupting one faithful entry's excess makes the forward leg fire",
          len(bad_p) == 1, "the plant is inert: the leg survived a corrupted excess")

    # C2 the degeneracy split is a real partition of the domain
    deg = [k for k, v in tr.items() if z(v["base"])]
    check("base == 0 and base > 0 partition the domain",
          len(deg) + (len(tr) - len(deg)) == len(tr) and 0 < len(deg) < len(tr),
          "deg=%d of %d" % (len(deg), len(tr)))

    # C2-PLANT: relabel one INFORMATIVE violator as degenerate and watch it leave the count --
    # the plant lands on the reading the sentence quotes, not on a list comprehension beside it
    def viol(TR, pos_only):
        out = []
        for k, v in TR.items():
            if not z(v["excess"]):
                continue
            if pos_only and z(v["base"]):
                continue
            g, p, p1, p2 = parts(k)
            if faithful(g, p, p1) and faithful(g, p, p2):
                continue
            out.append(k)
        return out

    vp = viol(tr, True)
    ka2 = vp[0]
    planted2 = dict(tr)
    planted2[ka2] = dict(planted2[ka2], base="0")
    check("C2-PLANT relabelling one informative violator as base == 0 removes it from the "
          "informative count",
          ka2 in [k for k in viol(tr, False)] and ka2 not in viol(planted2, True)
          and len(viol(planted2, True)) == len(vp) - 1,
          "the informative count does not read the degeneracy split")

    # C3 the naive law's record violators are non-empty at BOTH denominators
    V = [k for k, v in tr.items() if z(v["excess"])
         and not (faithful(parts(k)[0], parts(k)[1], parts(k)[2]) and faithful(parts(k)[0], parts(k)[1], parts(k)[3]))]
    VR = [k for k in V if k.split("|")[1] in record]
    VP = [k for k in VR if not z(tr[k]["base"])]
    check("the naive law is refuted by the RECORD space itself, not only by the constructed witness",
          len(VR) > 0 and len(VP) > 0, "record all=%d record base>0=%d" % (len(VR), len(VP)))

    # C4 the two 262s are two different sets
    ev_all = [k for k in tr
              if ori["%s|%s|%s" % (parts(k)[0], parts(k)[2], parts(k)[1])] != 0
              and ori["%s|%s|%s" % (parts(k)[0], parts(k)[3], parts(k)[1])] != 0]
    ev_rec = [k for k in ev_all if k.split("|")[1] in record]
    check("|evaluated over ALL protocols| == |record violators over the full domain| -- a count "
          "coincidence over two DISJOINT sets",
          len(ev_all) == len(VR) and not (set(ev_rec) & set(VR)),
          "ev_all=%d VR=%d inter(record)=%d" % (len(ev_all), len(VR), len(set(ev_rec) & set(VR))))

    # C5 the structural witness: T_raw == 0 everywhere, T_excess == 0 only on the degenerate half
    fr = V4.FRAGILE_REFERENCE
    ks = [k for k, v in tr.items() if k.split("|")[1] == fr]
    raw_zero = all(z(tr[k]["raw"]) for k in ks)
    ex_zero_deg = all(z(tr[k]["base"]) for k in ks if z(tr[k]["excess"]))
    check("the population-blind reference has T_raw == 0 in every entry while its T_excess is 0 "
          "only where base == 0",
          raw_zero and ex_zero_deg and any(not z(tr[k]["excess"]) for k in ks),
          "raw zero=%s excess-zero-all-degenerate=%s" % (raw_zero, ex_zero_deg))

    # C6 the evaluated set is DISJOINT from the record violators at the record level
    check("the record-level evaluated set and the record-level violator set are disjoint",
          not (set(ev_rec) & set(VR)), "intersection=%d" % len(set(ev_rec) & set(VR)))

    return {"items": log, "ok": ok, "total": total}


# ------------------------------------------------------------------------------------------------

def report_text(d):
    L = []
    A = L.append
    A("== issue #141 -- the naive transport law at the ENTRY level ==")
    A("   %d entries = %d games x %d populations-pairs x %d protocols (%d of record)"
      % (d["entries"], 9, 6, d["protocols"], d["record_protocols"]))
    A("")
    A("the domain, and the half of it that carries no information")
    A("   base == 0 (the two populations rank the payoff identically): %d of %d"
      % (d["base_zero"], d["entries"]))
    A("   base  > 0 : %d    base histogram: %s"
      % (d["base_positive"], dict(d["base_values"])))
    A("")
    A("the FORWARD leg (a theorem): faithful in both populations => excess == 0")
    A("   counterexamples over all %d entries: %d" % (d["entries"], d["forward_counterexamples_all"]))
    A("")
    A("the NAIVE law at entry level:  excess == 0  <=>  faithful in both populations")
    for label, nice in (("all", "full domain"), ("base_positive", "base > 0 (informative)")):
        A("   over %-22s violators %3d   of which record %3d, over %d record designs"
          % (nice, d["violators_" + label], d["violators_record_" + label],
             d["violators_record_%s_designs" % label]))
        bp = d["violators_record_%s_by_protocol" % label]
        if bp:
            A("      " + "  ".join("%s %d" % kv for kv in bp.items()))
    A("")
    A("the evaluated set C6c takes its converse reading over")
    A("   all protocols %d  | record only %d  %s"
      % (d["evaluated_all"], d["evaluated_record"], dict(d["evaluated_record_by_protocol"])))
    A("   intersect the record violators: %d   (|evaluated| == |record violators| : %s)"
      % (d["evaluated_record_intersect_record_violators"], d["count_coincidence"]))
    A("")
    A("the structural witness re-read: T_raw vs T_excess")
    for pr in (V4.FRAGILE_REFERENCE, V4.WITNESS, V4.CONSTRUCTED_WITNESS):
        A("   %-14s entries %d  T_raw ==0 in %d  T_excess ==0 in %d (of which base>0: %d)"
          % (pr, d["%s_entries" % pr], d["%s_raw_zero" % pr], d["%s_excess_zero" % pr],
             d["%s_excess_zero_base_positive" % pr]))
    A("")
    c = d["_certificate"]
    A("certificate %d/%d" % (c["ok"], c["total"]))
    L.extend(c["items"])
    return "\n".join(L) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    d, *_ = build()
    txt = report_text(d)
    print(txt, end="")
    if a.out:
        with open(a.out, "w") as fh:
            json.dump(d, fh, indent=1, sort_keys=True, default=str)
            fh.write("\n")
        sha = hashlib.sha256(open(a.out, "rb").read()).hexdigest()
        print("\nwrote %s  sha256 %s" % (a.out, sha[:16]))
    return 0 if d["_certificate"]["ok"] == d["_certificate"]["total"] else 1


if __name__ == "__main__":
    sys.exit(main())
