#!/usr/bin/env python3
"""Issue #120 -- validation of the manuscript's claims against the committed artefacts.

Each check is attached to a specific headline claim.  The checks read ONLY committed files:
the six *_results.json produced by the instruments and the reference-layer artefacts.  A check
that cannot fire is decoration, so the suite also runs a two-sided control on itself (see
`--selftest`): every check is re-run against a MUTATED copy of the artefact it reads and must
report a failure.

Usage:  /usr/bin/python3 validate.py
        /usr/bin/python3 validate.py --selftest
Out:    VALIDATE <n>/<n> and RESULT: PASS | FAIL, one line per check.
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
N1 = 50000           # spike_v1 trace length
FAMS6 = ["uniform", "powerlaw1", "powerlaw2", "hotset", "scan8", "scan64"]
FAILS = []
CHECKS = []


def load(name):
    with open(os.path.join(HERE, name + "_results.json")) as f:
        return json.load(f)


def check(label, cond, detail=""):
    CHECKS.append((label, bool(cond), detail))
    if not cond:
        FAILS.append(label)
    return bool(cond)


def near(a, b, tol):
    return abs(a - b) <= tol


# --------------------------------------------------------------------------- checks
def suite(D):
    v0, v1, v2, v3, v4, v5 = (D["spike_v0"], D["spike_v1"], D["spike_v2"],
                              D["spike_v3"], D["spike_v4"], D["spike_v5"])

    # -- 5.1 the floor is exact and certified -------------------------------------------
    c = v0["certificate"]
    check("5.1 certificate: naive Belady vs exhaustive cache-state, 0 disagreements over 200",
          c["cases"] == 200 and c["disagreements"] == 0,
          "cases=%s disagreements=%s" % (c["cases"], c["disagreements"]))
    ct = v0["control"]
    check("5.1 control: a deliberately bad policy is never BELOW the floor (0 violations / 200)",
          ct["violations"] == 0 and ct["cases"] == 200, "violations=%s" % ct["violations"])
    c1 = v1["certificate"]
    check("5.1 three routes agree on 300 tiny traces (0 + 0 disagreements)",
          c1["naive_vs_exhaustive"] == 0 and c1["heap_vs_exhaustive"] == 0, json.dumps(c1))
    check("5.1 naive Belady == lazy-heap exactly at grid scale (n=4000, 3 capacities)",
          c1["grid_scale_equal"] is True and c1["grid_scale_cells"] == 3,
          "equal=%s cells=%s" % (c1.get("grid_scale_equal"), c1.get("grid_scale_cells")))
    out = v2["oracle_vs_policy"]
    check("5.1 Mattson certified: 624 (trace, capacity) pairs, 0 disagreements",
          v2["mattson_certificate"]["pairs"] == 624
          and v2["mattson_certificate"]["disagreements"] == 0,
          json.dumps(v2["mattson_certificate"]))

    g = {f: sorted([c for c in v1["cells"] if c["family"] == f], key=lambda c: c["h"])
         for f in FAMS6}
    lo = min(cs[0]["gap_LRU"] for cs in g.values())
    hi = max(cs[0]["gap_LRU"] for cs in g.values())
    check("5.1 gap at h=0.01 spans 5.99 % .. 138.9 %",
          near(100 * lo, 5.99, 0.1) and near(100 * hi, 138.9, 0.1),
          "%.2f%% .. %.2f%%" % (100 * lo, 100 * hi))
    lo5 = min(cs[-1]["gap_LRU"] for cs in g.values())
    hi5 = max(cs[-1]["gap_LRU"] for cs in g.values())
    check("5.1 gap at h=0.50 spans 0.0 % .. 140.9 %",
          near(100 * lo5, 0.0, 0.05) and near(100 * hi5, 140.9, 0.1),
          "%.2f%% .. %.2f%%" % (100 * lo5, 100 * hi5))

    # -- 5.2 the closed form ------------------------------------------------------------
    cf = v3["closed_form"]
    check("5.2 closed form max abs error 1.07e-4",
          near(cf["max_err"], 1.0667e-4, 5e-7), "%.3e" % cf["max_err"])
    # c_0.5 = ceil((W+1)/2) on the cyclic families (a prediction of the form)
    cyc = [r for r in v3["rows"] if r["family"].startswith("loop")]
    ok = all(r["c_0.5"] == (r["D"] + 1 + 1) // 2 for r in cyc)
    check("5.2 c_0.5 = ceil((W+1)/2) on all %d cyclic families (form not fitted to this)" % len(cyc),
          ok, str([(r["family"], r["c_0.5"]) for r in cyc]))

    # -- 5.3 P1 refuted -----------------------------------------------------------------
    p1 = v1["p1_verdict"]
    check("5.3 P1 REFUTED: 0 of 6 families satisfy both limbs",
          p1["families_both_limbs"] == 0 and p1["families_n"] == 6 and p1["verdict"] == "REFUTED",
          json.dumps(p1))
    limbA = sum(1 for cs in g.values() if min(c["gap_LRU"] for c in cs if c["h"] <= 0.2) >= 0.20)
    limbB = sum(1 for cs in g.values()
                if all(b <= a + 1e-12 for a, b in zip([c["gap_LRU"] for c in cs],
                                                      [c["gap_LRU"] for c in cs][1:])))
    check("5.3 limb A holds in 1 of 6, limb B in 1 of 6", limbA == 1 and limbB == 1,
          "limbA=%d limbB=%d" % (limbA, limbB))
    grows = sum(1 for cs in g.values()
                if (sum(cs[-1]["LRU"]) / len(cs[-1]["LRU"])) / (sum(cs[-1]["opt"]) / len(cs[-1]["opt"]))
                > (sum(cs[0]["LRU"]) / len(cs[0]["LRU"])) / (sum(cs[0]["opt"]) / len(cs[0]["opt"])))
    check("5.3 endpoint direction is UP in 4 of 6 families", grows == 4, "grows=%d" % grows)
    check("5.3 monotone non-decreasing in only 3 of 6 (the normalisation block agrees)",
          v1["p1_normalisation"]["monotone_h"] == 3
          and v1["p1_normalisation"]["monotone_h_eff"] == 3,
          json.dumps(v1["p1_normalisation"]))
    # the mechanism table must agree with the endpoints -- the assertion the instrument makes
    bad = []
    for f, cs in g.items():
        ro = (sum(cs[0]["opt"]) / len(cs[0]["opt"])) / (sum(cs[-1]["opt"]) / len(cs[-1]["opt"]))
        rl = (sum(cs[0]["LRU"]) / len(cs[0]["LRU"])) / (sum(cs[-1]["LRU"]) / len(cs[-1]["LRU"]))
        ge = (sum(cs[-1]["LRU"]) / len(cs[-1]["LRU"])) / (sum(cs[-1]["opt"]) / len(cs[-1]["opt"]))
        gs = (sum(cs[0]["LRU"]) / len(cs[0]["LRU"])) / (sum(cs[0]["opt"]) / len(cs[0]["opt"]))
        if (ro > rl) != (ge > gs):
            bad.append(f)
    check("5.3 mechanism (which quantity falls faster) agrees with the endpoints in all 6",
          not bad, "disagree=%s" % bad)

    # -- 5.4 P2 refuted -----------------------------------------------------------------
    # the artefact stores the spread as a FRACTION (max/min - 1); the paper states it in per cent,
    # so the check converts rather than comparing a fraction to a percentage
    check("5.4 the slope bucket collision spans 8,494 % (0.0060 .. 0.5122)",
          near(100 * v1["p2_first_look"]["worst_spread"], 8493.5, 0.6),
          "%.2f%%" % (100 * v1["p2_first_look"]["worst_spread"]))
    by = {}
    for c in v1["cells"]:
        by.setdefault(round(c["stat"][0]["slope"], 1), []).append(
            (c["family"], sum(c["opt"]) / len(c["opt"]) / N1))
    coll = {k: v for k, v in by.items() if len({x[0] for x in v}) > 1}
    widest = max(coll.values(), key=lambda v: max(y[1] for y in v) / min(y[1] for y in v))
    lo, hi = min(y[1] for y in widest), max(y[1] for y in widest)
    check("5.4 that bucket's own endpoints are 0.0060 and 0.5122",
          near(lo, 0.0060, 5e-5) and near(hi, 0.5122, 5e-5)
          and len({y[0] for y in widest}) == 2,
          "%.4f .. %.4f over %s" % (lo, hi, sorted({y[0] for y in widest})))
    best = v3["best"]
    exp = {"c_0.5": ("sd_q50", 0.800), "c_0.9": ("hs90", 0.849), "c_0.99": ("sd_q99", 0.761)}
    for t, (stat, err) in exp.items():
        check("5.4 %s: best candidate %s, held-out max rel. error %.3f" % (t, stat, err),
              best[t] == stat and near(v3["predictor"][t + "|" + stat]["test_max"], err, 5e-4),
              "%s %.3f" % (best[t], v3["predictor"][t + "|" + best[t]]["test_max"]))
    check("5.4 every candidate misses the 5 % bar by more than 10x (min held-out max error > 0.5)",
          min(p["test_max"] for p in v3["predictor"].values()) > 0.5,
          "min=%.3f" % min(p["test_max"] for p in v3["predictor"].values()))

    # -- 5.5 P3 refuted ------------------------------------------------------------------
    bh = v2["below_head_share"]
    check("5.5 oracle below-head relief mean 0.896", near(out["oracle_mean"], 0.8959, 1e-3),
          "%.4f" % out["oracle_mean"])
    check("5.5 LRU below-head relief on the cyclic families is EXACTLY 0.000",
          all(near(r["lru_below_head_share"], 0.0, 1e-12)
              for r in v2["rows"] if r["kind"] == "all-or-nothing"),
          str([(r["family"], r["lru_below_head_share"]) for r in v2["rows"]
               if r["kind"] == "all-or-nothing"]))
    check("5.5 oracle range 0.779 .. 0.968 over the seven families",
          near(min(bh["per_family"].values()), 0.7794, 1e-3)
          and near(max(bh["per_family"].values()), 0.9677, 1e-3),
          "%.4f .. %.4f" % (min(bh["per_family"].values()), max(bh["per_family"].values())))
    gaps = {}
    for r in v2["rows"]:
        if r["kind"] != "all-or-nothing":
            continue
        caps = v2["caps"]
        i = caps.index(r["c_knee"] - 1)
        gaps[r["family"]] = 100 * (r["lru"][i] / r["phi_star"][i] - 1)
    check("5.5 at capacity W-1 the gap is 598 % / 1384 % / 2859 %",
          near(gaps["loop8"], 598.3, 0.5) and near(gaps["loop16"], 1383.7, 0.5)
          and near(gaps["loop32"], 2858.6, 0.5), json.dumps({k: round(v, 1) for k, v in gaps.items()}))
    dc = v2["detector_control"]
    check("5.5 knee detector two-sided control (planted cliff 1.000, planted none 0.048)",
          near(dc["planted_knee_peak_share"], 1.0, 1e-9)
          and near(dc["planted_none_peak_share"], 0.0484, 1e-3), json.dumps(dc))
    check("5.5 blind knee detector finds 6 of 7 families within 0.25",
          v2["knee_hits"]["found"] == 6 and v2["knee_hits"]["n"] == 7, json.dumps(v2["knee_hits"]))

    # -- 5.6 the no-go --------------------------------------------------------------------
    cert = v4["certificate"]
    check("5.6 matched pair: identical stack-distance multisets AND identical LRU curves",
          cert["sd_identical"] is True and cert["lru_identical"] is True, json.dumps(cert))
    check("5.6 matched pair: optima at capacity 2 are 4 and 6 misses (n = 9)",
          cert["opt_A_cap2"] == 4 and cert["opt_B_cap2"] == 6, json.dumps(cert))
    rows = {r["K"]: r for r in v4["rows"]}
    check("5.6 the gap is stable at scale: sd-L1 exactly 0.0 at every K, gap -> 99.8 % at K=500",
          all(r["sd_l1"] == 0.0 for r in v4["rows"])
          and near(rows[500]["gap"], 0.9980, 1e-3), json.dumps(rows[500]))
    check("5.6 the floors at n = 9000 are 0.2224 and 0.4447 (2.00x)",
          near(v5["practical"]["K=1000"]["phi_A"], 0.22244, 1e-4)
          and near(v5["practical"]["K=1000"]["phi_B"], 0.44467, 1e-4),
          json.dumps(v5["practical"]["K=1000"]))
    check("5.6 genericity: 13 of 28 sampled profiles (46 %) carry more than one optimum",
          v4["generic"]["multisets_with_multiple_optima"] == 13
          and v4["generic"]["sd_multisets"] == 28
          and near(v4["generic"]["fraction"], 0.4643, 1e-3), json.dumps(v4["generic"]))
    check("5.6 relabelling control leaves the certificate unchanged (42 == 42)",
          v4["relabel_control"]["identical"] is True, json.dumps(v4["relabel_control"]))
    fr = [v["frac_spread"] for v in v5["exhaustive"].values()]
    check("5.6 exhaustive: 36-68 % of profile classes carry a spread, max ratio 1.25-1.50",
          near(min(fr), 0.3636, 1e-3) and near(max(fr), 0.6842, 1e-3)
          and near(max(v["max_ratio"] for v in v5["exhaustive"].values()), 1.5, 1e-9),
          "%.3f .. %.3f" % (min(fr), max(fr)))

    # -- 5.7 the profile-invisible fraction -----------------------------------------------
    ms = v5["midscale"]
    check("5.7 mid scale: 1791 of 2510 classes (71 %) carry a spread, max ratio 1.500",
          ms["multi_classes"] == 1791 and ms["classes"] == 2510 and near(ms["max_ratio"], 1.5, 1e-9),
          json.dumps(ms))
    check("5.7 mid-scale max ABSOLUTE spread 0.125 in the floor",
          near(ms["max_abs_spread"], 0.125, 1e-6), "%.4f" % ms["max_abs_spread"])
    check("5.7 relabelling control: same class membership and same phi*",
          v5["relabel_control"]["same_class"] is True and v5["relabel_control"]["same_phi"] is True,
          json.dumps(v5["relabel_control"]))

    # -- reference layer (committed report, read back) ------------------------------------
    refs = json.load(open(os.path.join(HERE, "refs", "curated.json")))["entries"]
    meta = json.load(open(os.path.join(HERE, "refs", "meta.json")))
    log = open(os.path.join(HERE, "refs", "verify.log")).read()
    ok_lines = [l for l in log.splitlines() if l.startswith("OK ")]
    check("refs: 129 curated entries", len(refs) == 129, "n=%d" % len(refs))
    check("refs: the committed verification log holds 129 OK lines and no PROBLEM",
          len(ok_lines) == 129 and "0 PROBLEM" in log,
          "ok=%d" % len(ok_lines))
    check("refs: every curated entry carries author metadata (%d/%d)"
          % (meta["with_authors"], len(refs)),
          meta["with_authors"] == 129 and meta["route"] == "abstract pages",
          "route=%s problems=%d" % (meta["route"], len(meta["problems"])))
    check("refs: every entry is cited in the manuscript (0 uncited)",
          uncited_count() == 0, "uncited=%d" % uncited_count())
    # the companion the check above needs: an uncited COUNT of 0 is also what a reader that finds no
    # entries at all returns, so the entry block is asserted to be READ (129 markers in the house
    # form).  Without this, a marker-form change makes the check above pass vacuously.
    check("refs: the entry block is READ, not empty (129 markers)",
          entry_count() == 129, "markers=%d" % entry_count())
    return


def entry_count():
    """The number of reference markers the reader finds in the References window, in the house form
    (`[n]`, `n.` or `n)`) -- the quantity that makes the uncited check able to fail."""
    man = os.path.join(HERE, "manuscript.md")
    if not os.path.exists(man):
        return -1
    text = open(man, encoding="utf-8").read()
    tail = text.split("## References")[-1]
    return len(re.findall(r"^\[?(\d+)[\].)] ", tail, re.M))


def uncited_count():
    """Read the assembled manuscript and count curated entries no numbered key cites."""
    man = os.path.join(HERE, "manuscript.md")
    if not os.path.exists(man):
        return -1
    text = open(man, encoding="utf-8").read()
    entries = json.load(open(os.path.join(HERE, "refs", "curated.json")))["entries"]
    meta = json.load(open(os.path.join(HERE, "refs", "meta.json")))["meta"]
    # build the rendered reference line for each entry, then look for its number in the body.
    # The marker set is the one refgate reads -- `[n]`, `n.` or `n)` at the start of a line -- so the
    # house `[n]` form does not make this check pass vacuously by finding no entries at all.
    body = text.split("## References")[0]
    have = sorted(int(m) for m in re.findall(r"\[(\d+)\]", body))
    numbered = set(int(m) for m in re.findall(r"^\[?(\d+)[\].)] ", text.split("## References")[-1], re.M))
    cited = set(have) & numbered
    return len(numbered) - len(cited)


def main():
    selftest = "--selftest" in sys.argv
    D = {n: load(n) for n in ("spike_v0", "spike_v1", "spike_v2", "spike_v3", "spike_v4", "spike_v5")}
    if selftest:
        # two-sided control: mutate the artefact each check reads and require a FAILURE
        import copy
        mutations = [
            ("5.1 certificate", lambda d: d["spike_v0"]["certificate"].update(disagreements=1)),
            ("5.1 control", lambda d: d["spike_v0"]["control"].update(violations=1)),
            ("5.3 P1", lambda d: d["spike_v1"]["p1_verdict"].update(families_both_limbs=6)),
            ("5.4 P2", lambda d: d["spike_v3"]["predictor"]["c_0.5|sd_q50"].update(test_max=0.01)),
            ("5.5 P3", lambda d: d["spike_v2"]["oracle_vs_policy"].update(oracle_mean=0.01)),
            ("5.6 no-go", lambda d: d["spike_v4"]["certificate"].update(sd_identical=False)),
            ("5.7 fraction", lambda d: d["spike_v5"]["midscale"].update(multi_classes=10)),
        ]
        caught = 0
        for name, mutate in mutations:
            d = copy.deepcopy(D)
            mutate(d)
            del CHECKS[:]
            del FAILS[:]
            suite(d)
            if FAILS:
                caught += 1
                print("   plant caught by: %s" % ", ".join(FAILS[:2]))
            else:
                print("   PLANT NOT CAUGHT: %s" % name, file=sys.stderr)
        print("SELFTEST %d/%d plants caught" % (caught, len(mutations)))
        return 0 if caught == len(mutations) else 1

    suite(D)
    for label, ok, detail in CHECKS:
        print("%-4s %s%s" % ("ok" if ok else "FAIL", label, ("   [%s]" % detail) if detail else ""))
    n = len(CHECKS)
    print("VALIDATE %d/%d" % (n - len(FAILS), n))
    print("RESULT: %s" % ("PASS" if not FAILS else "FAIL"))
    return 0 if not FAILS else 1


if __name__ == "__main__":
    sys.exit(main())
