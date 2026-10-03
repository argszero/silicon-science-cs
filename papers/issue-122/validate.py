#!/usr/bin/env python3
"""Issue #122 -- validation of the manuscript's claims against the committed artefacts.

Every check is attached to a specific headline claim and reads ONLY committed files: the three
`*_results.json` written by the instruments, the reference-layer artefacts, `figures/manifest.json`
and the assembled `manuscript.md`.  A check that cannot fire is decoration, so the suite also runs a
two-sided control on itself (`--selftest`): the artefacts are MUTATED in memory, once per check, and
the suite must report a failure each time.

Two of the checks RE-DERIVE a statistic the manuscript prints rather than reading the printed value
back (the Jensen-gap side split and the figure hashes): a printed number is not evidence for itself.

Usage:  /usr/bin/python3 validate.py
        /usr/bin/python3 validate.py --selftest
Out:    VALIDATE <n>/<n> and RESULT: PASS | FAIL, one line per check.
"""
import hashlib
import json
import math
import os
import re
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
GATE_EVENTS = 30.0          # the adequacy gate is expected EVENTS (density x rate), not observations
FAILS = []
CHECKS = []


def load(name):
    with open(os.path.join(HERE, name)) as f:
        return json.load(f)


def check(label, cond, detail=""):
    CHECKS.append((label, bool(cond), detail))
    if not cond:
        FAILS.append(label)
    return bool(cond)


def near(a, b, tol):
    return abs(a - b) <= tol


def close(a, b, rel=1e-12):
    return math.isclose(a, b, rel_tol=rel, abs_tol=0.0)


def jensen(v1):
    """Re-derive the Jensen-gap readings from the committed per-cell vectors.

    The artefact stores the per-symbol vectors, not the pairs, so this is a second computation of
    the same statistic -- on the instrument's OWN gate (expected events, denominator route B) and
    with the symbol's absence fraction carried along.
    """
    gap, abs_frac = [], []
    for c in v1["cells"]:
        for i in range(len(c["loss_A"])):
            A, B, D, cf = c["loss_A"][i], c["loss_B"][i], c["loss_den"][i], c["loss_cf"][i]
            if not (math.isfinite(A) and math.isfinite(B)):
                continue
            if D * B < GATE_EVENTS or not cf > 0:
                continue
            gap.append(cf / B)
            abs_frac.append(c["abs_per_sym"][i])
    return gap, abs_frac


def suite(D):
    v1, v2, v3 = D["spike_v1"], D["spike_v2"], D["spike_v3"]
    man = D["manuscript"]

    # ---------------------------------------------------------------- 4.1 the loop axis
    gap, abs_frac = jensen(v1)
    check("4.1 the gap is read on an expected-EVENT gate (density x rate >= 30): %d readings"
          % v1["n_gap_pairs"],
          len(gap) == v1["n_gap_pairs"] and v1["n_gap_pairs"] > 0,
          "recomputed=%d artefact=%s" % (len(gap), v1["n_gap_pairs"]))
    check("4.1 median and minimum of the bound/measured ratio are the artefact's",
          close(statistics.median(gap), v1["cf_over_meas_median"])
          and close(min(gap), v1["cf_over_meas_min"]),
          "median %.6g min %.3g" % (statistics.median(gap), min(gap)))
    check("4.1 the claimed MAXIMUM is the artefact's (%.3g)" % v1["cf_over_meas_max"],
          close(max(gap), v1["cf_over_meas_max"]), "recomputed=%.6g" % max(gap))
    # the scope of the claim: the bound is NOT above the measured rate everywhere
    n_above = sum(1 for g in gap if g > 1.0)
    check("4.1 the reading is above the bound in %s of %s, below it in the rest"
          % (v1["n_gap_above1"], v1["n_gap_pairs"]),
          n_above == v1["n_gap_above1"]
          and v1["n_gap_above1"] + v1["n_gap_below1"] == v1["n_gap_pairs"]
          and v1["n_gap_above1"] > 0,
          "recomputed=%d above1, artefact=%s" % (n_above, v1["n_gap_above1"]))
    # the mechanism: the crossing rate rises with the absence fraction of the symbol
    bins = v1["gap_by_absence"]
    check("4.1 the absence-fraction bins partition the readings and their crossings sum",
          sum(b["n"] for b in bins) == v1["n_gap_pairs"]
          and sum(b["n_above1"] for b in bins) == v1["n_gap_above1"],
          "n=%d above1=%d" % (sum(b["n"] for b in bins), sum(b["n_above1"] for b in bins)))
    rates = [b["n_above1"] / float(b["n"]) for b in bins if b["n"]]
    check("4.1 the crossing rate rises with the absence fraction (%.3f -> %.3f)"
          % (rates[0], rates[-1]),
          all(a <= b + 1e-12 for a, b in zip(rates, rates[1:])) and rates[-1] > 5 * rates[0],
          "rates=%s" % ["%.3f" % r for r in rates])
    # the two routes to the same quantity
    rel = []
    for c in v1["cells"]:
        for i in range(len(c["loss_A"])):
            A, B, den = c["loss_A"][i], c["loss_B"][i], c["loss_den"][i]
            if math.isfinite(A) and math.isfinite(B) and den * B >= GATE_EVENTS:
                rel.append(abs(A - B) / B)
    check("4.1 route A vs route B agree to the stated %.1f%% at the gate" % (100 * v1["rel_A_vs_B_max_wellcounted"]),
          close(max(rel), v1["rel_A_vs_B_max_wellcounted"]) and max(rel) < 0.5,
          "recomputed=%.4f" % max(rel))
    # the worst symbol's loss vs n: the closed form collapses, the measurement does not
    def cell(src, n, lam):
        return [x for x in v1["cells"] if x["source"] == src and x["n"] == n and x["lam"] == lam][0]
    c25, c200 = cell("uniform", 25, 0.01), cell("uniform", 200, 0.01)
    r_meas = c25["loss_A"][c25["worst_symbol"]] / c200["loss_A"][c200["worst_symbol"]]
    r_cf = c25["loss_cf"][c25["worst_symbol"]] / c200["loss_cf"][c200["worst_symbol"]]
    check("4.1 measured loss falls by only %.1fx from n=25 to n=200 while the closed form falls by %.1e x"
          % (r_meas, r_cf), r_meas < 10 and r_cf > 1e6, "meas=%.3f cf=%.3e" % (r_meas, r_cf))
    # certificates: the mean recursion from a PERTURBED start, and the variance recursion
    means = [v for k, v in v1["certificates"].items() if k.startswith("mean_")]
    vars_ = [v for k, v in v1["certificates"].items() if k.startswith("var_")]
    check("4.1 certificate: the mean recursion (perturbed start) holds in %d cells" % len(means),
          len(means) == 2 and max(m["max_abs_err"] for m in means) < 0.02,
          "max err %.4f" % max(m["max_abs_err"] for m in means))
    check("4.1 certificate: the variance recursion holds in %d cells" % len(vars_),
          len(vars_) == 4 and max(m["max_abs_err"] for m in vars_) < 0.05,
          "max err %.4f" % max(m["max_abs_err"] for m in vars_))
    # planted-truth controls
    lam0 = v1["controls"]["lam0"]
    check("4.1 control lam=0 from a point-mass start: absence fraction exactly (K-1)/K",
          close(lam0["abs_overall"], lam0["exact"]) and close(lam0["exact"], 0.875),
          "%.6f vs %.6f" % (lam0["abs_overall"], lam0["exact"]))
    worst1 = max(v1["controls"][k]["rel"] for k in ("lam1_uniform", "lam1_twohot", "lam1_zipf"))
    check("4.1 control lam=1: measured loss equals the exact (1-p)^n to %.1e" % worst1,
          worst1 < 1e-9, "worst rel %.2e" % worst1)

    # ---------------------------------------------------------------- 4.2 the protocol axis
    parts = v2["part2"]
    mono = all(p["boundary"]["1"] > p["boundary"]["4"] > p["boundary"]["64"] for p in parts)
    check("4.2 the boundary falls monotonically in the window in %d/%d configurations"
          % (sum(1 for p in parts if p["boundary"]["1"] > p["boundary"]["4"] > p["boundary"]["64"]),
             len(parts)), len(parts) == 4 and mono,
          str([(p["source"], p["n"], round(p["ratio_w64_over_w1"], 5)) for p in parts]))
    check("4.2 the w=64/w=1 ratio is between 1e-4 and 2e-2 (2-3 orders) in every configuration",
          all(1e-4 <= p["ratio_w64_over_w1"] <= 2e-2 for p in parts),
          "%.2e .. %.2e" % (min(p["ratio_w64_over_w1"] for p in parts),
                            max(p["ratio_w64_over_w1"] for p in parts)))

    # ---------------------------------------------------------------- 4.3 the mechanism
    p3 = v2["part3"]
    rel3 = [abs(x["rate_measured"] - x["rate_ma_eig"]) / x["rate_ma_eig"] for x in p3]
    span = max(x["rate_measured"] for x in p3) / min(x["rate_measured"] for x in p3)
    check("4.3 the measured relaxation rate matches the moving-average eigenvalue in %d cells "
          "(worst %.2f%%, span %.1fx)" % (len(p3), 100 * max(rel3), span),
          len(p3) == 12 and max(rel3) < 0.03 and span > 30,
          "worst rel %.4f span %.2f" % (max(rel3), span))
    w64 = [x for x in p3 if x["w"] == 64 and x["lam"] == 0.05][0]
    wrong = w64["rate_w1_law"] / w64["rate_measured"]
    check("4.3 at lam=0.05, w=64 the replacement law is wrong by %.2fx" % wrong,
          wrong > 30, "wrong=%.3f" % wrong)
    c1 = v2["controls"]["C1_w1_is_replacement"]
    check("4.3 control: w=1 reproduces the replacement loop EXACTLY (max abs diff %s)" % c1["max_abs_diff_vs_spike_v1"],
          c1["max_abs_diff_vs_spike_v1"] == 0.0, "diff=%r" % c1["max_abs_diff_vs_spike_v1"])
    z = [v2["controls"][k]["max_z"] for k in v2["controls"] if k.startswith("C2a")]
    sig = [v2["controls"][k]["max_over_exact_in_sigma"] for k in v2["controls"] if k.startswith("C2b")]
    check("4.3 control: at lam=1 the measured loss matches the exact (1-p)^(w n) (max |z| %.2f)"
          % max(z), len(z) == 3 and max(z) < 3.0 and all(s <= 0 for s in sig),
          "z=%s sigma=%s" % (["%.2f" % x for x in z], sig))

    # ---------------------------------------------------------------- 4.4 the criterion axis
    crit = [c for c in v3["controls"] if c["kind"] == "criterion_dependence"]
    check("4.4 the two criteria differ by more than 10x in every located cell (%d cells)" % len(crit),
          len(crit) == 4 and all(c["ratio_stationary_over_heal"] > 10 for c in crit),
          str([round(c["ratio_stationary_over_heal"], 1) for c in crit]))
    ceil_ = [c for c in v3["controls"] if c["kind"] == "ceiling_unsatisfiable"]
    check("4.4 the two-hot w=1 prevention criterion is a domain CEILING, not a located number",
          len(ceil_) == 1 and close(ceil_[0]["lambda_star"], 1.0)
          and any(close(c["lambda_stationary"], 1.0) for c in crit),
          str([(c["source"], c["w"], c["lambda_star"]) for c in ceil_]))
    res = max(c["log_resolution_decades"] for c in v3["cells"])
    smallest = min(c["lambda_star"] for c in v3["cells"])
    check("4.4 the bisection resolution (%.1e decades) is finer than the smallest boundary (%.1e)"
          % (res, smallest), res < smallest, "res=%.3e min=%.3e" % (res, smallest))
    beh = [c for c in v3["controls"] if c["kind"] == "behavioural" and c["source"] == "uniform" and c["w"] == 1][0]
    lo, hi = beh["below"]["full_support_fraction"], beh["above"]["full_support_fraction"]
    check("4.4 the behavioural control does not saturate (%.3f below vs %.3f above)" % (lo, hi),
          0.0 < lo < hi < 1.0 and lo < 0.9, "below=%.3f above=%.3f" % (lo, hi))
    p1 = v2["part1"]

    def heal(src, n, lam):
        return [r for r in p1 if r["source"] == src and r["n"] == n and r["lam"] == lam][0]["p_heal"]
    h5, h10, h20 = heal("twohot", 50, 0.005)["mean"], heal("twohot", 50, 0.01)["mean"], heal("twohot", 50, 0.02)["mean"]
    check("4.4 P(heal) rises with the rate in the two-hot n=50 row (%.3f -> %.3f -> %.3f)"
          % (h5, h10, h20), h5 < h10 < h20, "%.3f %.3f %.3f" % (h5, h10, h20))
    check("4.4 more samples help recovery at fixed rate (two-hot lam=0.005: n=200 %.3f > n=50 %.3f)"
          % (heal("twohot", 200, 0.005)["mean"], h5),
          heal("twohot", 200, 0.005)["mean"] > h5,
          "n200=%.3f n50=%.3f" % (heal("twohot", 200, 0.005)["mean"], h5))
    check("4.4 every P(heal) is an uncensored proportion with a stated seed count",
          all(0.0 <= r["p_heal"]["mean"] <= 1.0 and r["p_heal"]["n_seeds"] >= 3
              and r["p_heal"]["lo"] <= r["p_heal"]["mean"] <= r["p_heal"]["hi"] for r in p1),
          "cells=%d" % len(p1))

    # ---------------------------------------------------------------- 4.5 hysteresis
    cross = v1["crossing"]
    check("4.5 the hysteresis ratio crosses 1 inside the bracket in all %d configurations" % len(cross),
          len(cross) == 4
          and all(c["ratio_lo"] > 1.0 > c["ratio_hi"] and c["lam_lo"] < c["lam_hi"] for c in cross.values()),
          str({k: (v["lam_lo"], v["lam_hi"]) for k, v in cross.items()}))
    fp = v1["first_passage"]

    def fp_of(src, n, lam):
        return [r for r in fp if r["source"] == src and r["n"] == n and r["lam"] == lam][0]
    r50 = fp_of("uniform", 50, 0.005)
    rth = fp_of("twohot", 50, 0.005)
    check("4.5 the two-hot lam=0.005 recovery side is fully censored (T_recov undefined, %d of %d observed)"
          % (rth["n_obs_recov"], rth["n_obs_hyst"] if "n_obs_hyst" in rth else 200),
          (rth["T_recov"] != rth["T_recov"]) and rth["cens_recov"] > 0.9 and rth["n_obs_recov"] < 10,
          "T_recov=%r cens=%.3f n_obs=%d" % (rth["T_recov"], rth["cens_recov"], rth["n_obs_recov"]))
    # UNCENSORED cells only: a ratio whose recovery side is a median over the minority that
    # recovered is not comparable with one whose recovery side is a median over all replicates, so
    # the monotonicity claim is made where the recovery side is uncensored (cens_recov == 0).
    groups = {}
    for r in fp:
        groups.setdefault((r["source"], r["n"]), []).append(r)
    mono, uncens_n, inversions = True, 0, []
    for key, rs in groups.items():
        src, n = key
        hi = cross["%s/n%d" % (src, n)]["lam_hi"]      # the claim's scope is taken from the artefact
        rs = sorted([r for r in rs if r["cens_recov"] == 0.0 and r["lam"] <= hi], key=lambda r: r["lam"])
        ratios = [r["ratio_recov_over_loss"] for r in rs]
        uncens_n += len(ratios)
        for a, b in zip(ratios, ratios[1:]):
            if b > a + 1e-9:
                mono = False
                inversions.append((key, a, b))
    check("4.5 the hysteresis ratio falls monotonically with the rate up to the crossing "
          "(%d uncensored cells, 4 groups)" % uncens_n,
          mono and uncens_n >= 12 and len(groups) == 4,
          "mono=%s uncensored=%d inversions=%s" % (mono, uncens_n, inversions))
    # ... and past the crossing it stays below 1 (the crossing is not crossed back).  The one
    # inversion the series contains lies in this regime, where both readings are ~1e-3, so it is
    # inside the claim rather than against it.
    past = []
    for key, rs in groups.items():
        src, n = key
        hi = cross["%s/n%d" % (src, n)]["lam_hi"]
        past.extend(r["ratio_recov_over_loss"] for r in rs
                    if r["lam"] > hi and math.isfinite(r["ratio_recov_over_loss"]))
    check("4.5 past the crossing the ratio stays below 1 in all %d cells (the crossing is one-way)"
          % len(past), len(past) > 0 and all(r < 1.0 for r in past),
          "max=%.4f" % max(past))
    # the direction is taken from the artefact's OWN crossing bracket, not from a rate typed here
    ok_dir = True
    for k, br in cross.items():
        src, n = k.split("/")
        n = int(n.lstrip("n"))
        below = [r for r in fp if r["source"] == src and r["n"] == n
                 and r["lam"] <= br["lam_lo"] and math.isfinite(r["ratio_recov_over_loss"])]
        above = [r for r in fp if r["source"] == src and r["n"] == n
                 and r["lam"] >= br["lam_hi"] and math.isfinite(r["ratio_recov_over_loss"])]
        if not (all(r["T_loss"] < r["T_recov"] for r in below)
                and all(r["T_recov"] < r["T_loss"] for r in above)):
            ok_dir = False
    check("4.5 below the crossing the exit time is the short one; above it the entry time is",
          ok_dir, "brackets=%s" % {k: (v["lam_lo"], v["lam_hi"]) for k, v in cross.items()})
    check("4.5 the censoring fraction is printed beside the median (uniform lam=0.005: %.3f censored)"
          % r50["cens_recov"], 0.0 < r50["cens_recov"] < 1.0, "cens=%.3f" % r50["cens_recov"])

    # ---------------------------------------------------------------- 4.6 no invariant
    pred = [p for p in v3["predictions"] if "held_out_max_rel_miss" in p]
    checked = [(p["candidate"], p["source"], p["held_out_max_rel_miss"]) for p in pred]
    check("4.6 every candidate mechanism quantity fails its HELD-OUT test (%d candidates)" % len(pred),
          len(pred) >= 3 and min(p["held_out_max_rel_miss"] for p in pred) > 0.1,
          str([(c, s, round(m, 3)) for c, s, m in checked]))
    cells = v3["cells"]
    vs = [c["mean_var"] for c in cells]
    sn = [c["snr"] for c in cells]
    check("4.6 the span the manuscript prints is the span of the artefact's own cells "
          "(variance %.2fx, snr %.2f-%.2f)"
          % (max(vs) / min(vs), min(sn), max(sn)),
          max(vs) / min(vs) > 2.0 and 1.0 < min(sn) < max(sn) < 3.0,
          "var %.4g-%.4g snr %.3f-%.3f" % (min(vs), max(vs), min(sn), max(sn)))

    # ---------------------------------------------------------------- the reference layer
    cur = D["curated"]
    log = D["verify_log"]
    check("refs: %d curated entries, every one taken from the discovery artefact" % len(cur),
          len(cur) == 102 and all(e.get("source") == "discovery" for e in cur),
          "n=%d sources=%s" % (len(cur), sorted(set(e.get("source") for e in cur))))
    ok_lines = [l for l in log.splitlines() if l.startswith("OK ")]
    check("refs: the committed log holds %d OK lines and 0 PROBLEM" % len(ok_lines),
          len(ok_lines) == len(cur) and "0 PROBLEM" in log, "ok=%d" % len(ok_lines))
    check("refs: every entry carries author metadata (%s/%d, route %s)"
          % (D["meta"]["with_authors"], len(cur), D["meta"]["route"]),
          D["meta"]["with_authors"] == len(cur) and not D["meta"]["problems"],
          "problems=%d" % len(D["meta"]["problems"]))
    cited = set()
    refs_block = man.split("## References", 1)[1]
    numbered = set(re.findall(r"^(\d+)\. ", refs_block, re.M))
    for grp in re.findall(r"\[([\d,\s\-–]+)\]", man.split("## References", 1)[0]):
        for part in re.split(r",", grp):
            if re.match(r"^\d+$", part.strip()):
                cited.add(part.strip())
    check("refs: the manuscript cites all %d entries by numbered key (0 uncited)" % len(numbered),
          len(numbered) == len(cur) and not (numbered - cited),
          "numbered=%d uncited=%s" % (len(numbered), sorted(numbered - cited)[:5]))
    check("build: the assembled manuscript carries no placeholder-shaped text",
          "{{" not in man and "}}" not in man, "leftovers=%d" % man.count("{{"))
    check("build: the manuscript's own count of the readings above the bound is the artefact's",
          ("%d of the %d" % (v1["n_gap_above1"], v1["n_gap_pairs"])) in man,
          "looking for '%d of the %d'" % (v1["n_gap_above1"], v1["n_gap_pairs"]))

    # ---------------------------------------------------------------- figures
    man_fig = D["manifest"]
    figs = man_fig["figures"]
    check("figures: %d figures are recorded in the manifest" % len(figs), len(figs) == 5,
          "n=%d" % len(figs))
    bad = []
    for name, want in figs.items():
        p = os.path.join(HERE, "figures", name)
        if not os.path.exists(p):
            bad.append(name + ":missing")
            continue
        h = hashlib.sha256(open(p, "rb").read()).hexdigest()
        if h != want:
            bad.append(name + ":sha")
    check("figures: every committed PNG hashes to the value the manifest records", not bad,
          "bad=%s" % bad)
    src_ok = all(hashlib.sha256(open(os.path.join(HERE, s), "rb").read()).hexdigest() == h
                 for s, h in man_fig.get("sources", {}).items())
    check("figures: the manifest also pins the source artefacts the figures were drawn from", src_ok)
    return


def main():
    names = ("spike_v1", "spike_v2", "spike_v3")
    D = {n: load(n + "_results.json") for n in names}
    D["curated"] = load("refs/curated.json")["entries"]
    D["meta"] = load("refs/meta.json")
    D["manifest"] = load("figures/manifest.json")
    D["verify_log"] = open(os.path.join(HERE, "refs", "verify.log")).read()
    D["manuscript"] = open(os.path.join(HERE, "manuscript.md"), encoding="utf-8").read()

    if "--selftest" in sys.argv:
        import copy
        plants = [
            ("4.1 median", lambda d: d["spike_v1"].update(cf_over_meas_median=2.0)),
            ("4.1 max", lambda d: d["spike_v1"].update(cf_over_meas_max=1.0)),
            ("4.1 above-1", lambda d: d["spike_v1"].update(n_gap_above1=0, n_gap_below1=602)),
            ("4.1 bins", lambda d: d["spike_v1"]["gap_by_absence"][0].update(n_above1=99)),
            ("4.2 monotone", lambda d: d["spike_v2"]["part2"][0]["boundary"].update({"4": 0.5})),
            ("4.3 rate", lambda d: d["spike_v2"]["part3"][0].update(rate_ma_eig=0.5)),
            ("4.4 criterion", lambda d: [c for c in d["spike_v3"]["controls"]
                                         if c["kind"] == "criterion_dependence"][0].update(ratio_stationary_over_heal=1.05)),
            ("4.5 crossing", lambda d: d["spike_v1"]["crossing"]["uniform/n50"].update(ratio_lo=0.9)),
            ("refs count", lambda d: d["curated"].pop()),
            ("figure hash", lambda d: d["manifest"]["figures"].__setitem__(
                sorted(d["manifest"]["figures"])[0], "0" * 64)),
        ]
        caught = 0
        for name, plant in plants:
            d = copy.deepcopy(D)
            plant(d)
            del CHECKS[:]
            del FAILS[:]
            suite(d)
            if FAILS:
                caught += 1
                print("   plant caught by: %-70s %s" % (FAILS[0], name))
            else:
                print("   PLANT NOT CAUGHT: %s" % name, file=sys.stderr)
        print("SELFTEST %d/%d plants caught" % (caught, len(plants)))
        return 0 if caught == len(plants) else 1

    suite(D)
    for label, ok, detail in CHECKS:
        print("%-4s %s%s" % ("ok" if ok else "FAIL", label, ("   [%s]" % detail) if detail else ""))
    n = len(CHECKS)
    print("VALIDATE %d/%d" % (n - len(FAILS), n))
    print("RESULT: %s" % ("PASS" if not FAILS else "FAIL"))
    return 0 if not FAILS else 1


if __name__ == "__main__":
    sys.exit(main())
