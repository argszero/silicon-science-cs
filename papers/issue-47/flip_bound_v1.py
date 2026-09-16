#!/usr/bin/env python3
"""Issue #47 -- criterion (d)'s FLIP-COUNT BOUND, computed per headline number.

    python3 flip_bound_v1.py              # compute + write flip_bound_v1_results.json
    python3 flip_bound_v1.py --selftest   # offline: the bound's own behaviour on planted verdicts

WHY THIS FILE EXISTS.  The registration's fourth success criterion promises a *flip count* per
headline number -- how many of the observations a number rests on would have to change for its
VERDICT to reverse -- and through R346 no stage computed it: the manuscript said so ("stated as owed
rather than as read").  A margin that has not been measured is not a margin.

WHAT A FLIP BOUND IS HERE, stated before it is computed.

* The **unit** is the smallest observation the stage that produced the number actually records, and it
  is named per number (a block, a cluster, a profile, a comparable pair).  The bound is therefore in
  units OF THAT NUMBER, not in a unit chosen for convenience.
* A unit is **inverted** by giving its contribution the mirror value: the effect running the other way
  with the same magnitude.  Inversions are applied in DESCENDING order of how much the unit supports
  the verdict, so the number found is the FEWEST changes that could reverse it.
* The **verdict** is the decision rule printed next to the number in the manuscript, written out here
  as a function so the two cannot drift.
* **The direction matters, and both are reported.**  A verdict that ASSERTS an effect is falsified by
  evidence against it, so its bound is `k_inversions` (fewest unit inversions that reverse it).  A
  verdict that asserts an ABSENCE (a limit, a "not resolvable") cannot be reversed by inversions at
  all -- it is reversed by MORE support -- so for those the honest reading is
  `distance_to_boundary`: how far the observation sits from the decision boundary, in the number's own
  units.  Reporting a flip count for a negative verdict would be a made-up number; reporting nothing
  would hide the margin.  Where a verdict has two legs, the binding one (the smaller) is reported
  together with both.
* Where the recorded aggregate is the only thing the stage keeps (a cluster mean with its interval,
  not the cluster values), the bound is an ESTIMATE under a stated assumption and says so; where the
  units are recorded individually the bound is EXACT.

Outputs `flip_bound_v1_results.json` (committed, shipped and digested by `reproduce.sh`).
"""
import io
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "flip_bound_v1_results.json")
SUF = "sufficiency_v1_results.json"
EXT = "external_cell_v1_results.json"

T95 = 2.0244          # t_{0.975} at 38 d.o.f., the witness's block count
RATIO_BAR = 2.0       # the registered reading of a resolvable contrast (advantage / cluster MDE)


def load(name):
    return json.load(io.open(os.path.join(HERE, name), encoding="utf-8"))


def t_interval(xs, t=T95):
    n = len(xs)
    m = sum(xs) / n
    var = sum((x - m) ** 2 for x in xs) / (n - 1) if n > 1 else 0.0
    se = math.sqrt(var / n)
    return m, m - t * se, m + t * se


def interval_excludes_zero(xs):
    m, lo, hi = t_interval(xs)
    return lo > 0.0 or hi < 0.0


def min_inversions_count(flags, need):
    """Fewest units to flip in a count rule: the count must fall to `need - 1`.

    For a count rule the ORDER does not matter -- inverting any supporting unit removes exactly one
    from the count -- so the bound is how far the count stands above the threshold.
    """
    have = sum(1 for f in flags if f)
    return max(0, have - (need - 1))


def min_inversions_interval(values, invert):
    """Fewest unit inversions that make the interval contain 0.

    Strongest-support-first: inverting a large-magnitude unit moves the mean furthest, so a greedy
    sweep over descending |value| finds the minimum.  Returns None when the verdict already fails
    (nothing to reverse), and len+1 when no sweep reverses it.
    """
    xs = list(values)
    if not interval_excludes_zero(xs):
        return 0
    order = sorted(range(len(xs)), key=lambda i: -abs(xs[i]))
    for k in range(1, len(xs) + 1):
        xs[order[k - 1]] = invert(xs[order[k - 1]])
        if not interval_excludes_zero(xs):
            return k
    return len(xs) + 1


def witness_bound(suf):
    """F1.1 -- the scalar-insufficiency witness.  Unit: one of the 39 blocks, and within it the
    median over its own paired observations."""
    B = suf["part_B_matched_magnitude_witness"]["blocks"]
    med = [b["median_ratio_diff_plus_minus"] for b in B]
    over = [abs(b["median_ratio_diff_plus_minus"]) > b["mde_cluster_unit"] for b in B]
    n = len(B)
    need = n // 2 + 1
    k_count = min_inversions_count(over, need)
    k_interval = min_inversions_interval(med, lambda v: -v)
    per_block = sorted({b["n_pairs"] for b in B})
    obs = per_block[0] // 2 + 1 if len(per_block) == 1 else None
    return {
        "unit": "block (a problem x profile cell; %d of them, each block's median taken over its own "
                "%s paired observations)" % (n, " / ".join(str(p) for p in per_block)),
        "asserts": "an effect (the sign channel is resolvable)",
        "legs": {
            # each leg carries its OWN observation bound: quoting the binding leg's number beside
            # the other leg's name is exactly the mislabel the first version of the prose made
            "count": {"rule": "a MAJORITY of blocks (%d of %d) have |loss gap| above their own cluster "
                              "MDE" % (need, n),
                      "value": "%d of %d" % (sum(over), n), "k_inversions": k_count,
                      "k_paired_observations_lower_bound": k_count * obs if obs else None,
                      "kind": "exact (the blocks are recorded individually)"},
            "interval": {"rule": "the 95%% interval over the %d block medians excludes 0" % n,
                         "value": [round(x, 6) for x in t_interval(med)],
                         "k_inversions": k_interval,
                         "k_paired_observations_lower_bound": k_interval * obs if obs else None,
                         "kind": "exact (the blocks are recorded individually)"},
        },
        "k_inversions": min(k_count, k_interval),
        "binding_leg": "count" if k_count <= k_interval else "interval",
        "paired_observations_per_inverted_block": "%d of %d" % (obs, per_block[0]) if obs else None,
        "paired_observations_rule": (
            "a median over %d paired observations is inverted only if more than half of them move"
            % per_block[0]) if obs else None,
        "note": "the IDENTITY leg of this claim (the scalar-feature gap is exactly 0 in every block) "
                "has no flip bound: no change to the streams can move a quantity that is 0 by "
                "construction, and that is the stronger statement",
    }


def contrast_bound(suf):
    """F1.2 -- the sign channel, per problem.  Unit: a cluster of the contrast stage; the stage keeps
    the cluster MEAN and its interval, not the cluster values, so those bounds are estimates."""
    rows = suf["part_C2_clean_and_confounded_contrasts"]["contrast_b_clean"]
    out = {}
    for r in rows:
        if "even2" not in r["contrast"]:
            continue
        p, n = r["problem"], r["n_clusters"]
        lo, hi = r["ci95_cluster_unit"]
        m = r["median_advantage_odd"]
        mde = r["mde_cluster_unit"]
        ratio = r["advantage_vs_MDE_cluster"]
        # leg 1: the interval must reach 0 (an inversion of k clusters moves the mean by 2k*mean/n)
        k_int = math.ceil(lo * n / (2.0 * m)) if m > 0 else None
        # leg 2: the advantage must fall below the 2-MDE bar
        k_bar = math.ceil((ratio - RATIO_BAR) * mde * n / (2.0 * m)) if m > 0 and ratio > RATIO_BAR else None
        asserts = bool(r["resolvable_cluster_unit"] and ratio > RATIO_BAR)
        v = {
            "unit": "cluster (%d per row; the stage records the cluster mean and its interval only)" % n,
            "asserts": "an effect" if asserts else "an ABSENCE (this problem is not resolved)",
            "rule": "the row's 95%% cluster interval excludes 0 AND the advantage exceeds %d cluster "
                    "MDEs (the registered reading of a resolvable contrast)" % int(RATIO_BAR),
            "value": {"advantage_vs_mde": round(ratio, 4),
                      "ci95_cluster_unit": [round(lo, 6), round(hi, 6)],
                      "resolvable": bool(r["resolvable_cluster_unit"])},
        }
        if asserts:
            cands = [k for k in (k_int, k_bar) if k is not None]
            v.update({"k_inversions": min(cands), "legs": {
                "interval_reaches_zero": {"k_inversions": k_int,
                                          "kind": "ESTIMATE (equal-magnitude mean shift)"},
                "advantage_falls_below_the_bar": {"k_inversions": k_bar,
                                                  "kind": "ESTIMATE (equal-magnitude mean shift)"}},
                "binding_leg": "interval_reaches_zero" if (k_bar is None or k_int <= k_bar)
                else "advantage_falls_below_the_bar",
                "kind": "ESTIMATE -- the stage records the cluster mean and interval, not the cluster "
                        "values, so the mean-shift is assumed to come from equal-magnitude inversions"})
        else:
            v.update({"k_inversions": None,
                      "distance_to_boundary": round(RATIO_BAR - ratio, 4),
                      "distance_rule": "the observed ratio sits this many cluster MDEs BELOW the %d-MDE "
                                       "bar; only MORE support moves it across, so no inversion bound "
                                       "exists for this verdict" % int(RATIO_BAR),
                      "kind": "exact distance (from the recorded ratio), no inversion bound"})
        out[p] = v
    return out


def ordering_bound(ext):
    """F1.3 -- the external cell's ordering, per problem.  Unit: a comparable PAIR of profiles,
    recomputed from the recorded rows, so the bound is exact."""
    out = {}
    for p, rows in ext["cells"].items():
        g = [r["mean_gain"] for r in rows]
        t = [-r["worst_unit_degradation"] for r in rows]
        conc = disc = 0
        for i in range(len(rows)):
            for j in range(i + 1, len(rows)):
                a, b = g[i] - g[j], t[i] - t[j]
                if a == 0 or b == 0:
                    continue
                if a * b > 0:
                    conc += 1
                else:
                    disc += 1
        P = conc + disc
        tau = (conc - disc) / P if P else None
        out[p] = {
            "unit": "comparable pair of profiles (%d pairs over %d profiles; ties dropped)"
                    % (P, len(rows)),
            "asserts": "an effect (the ordering is concordant)",
            "rule": "Kendall tau of mean gain against the tail read as higher-is-better is > 0",
            "value": {"tau": round(tau, 4) if tau is not None else None,
                      "concordant": conc, "discordant": disc, "pairs": P},
            "k_inversions": max(0, math.ceil((conc - disc) / 2.0)) if tau is not None else None,
            "kind": "exact (every pair is recomputed from the recorded rows)",
        }
    return out


def reach_bound(ext):
    """L3 -- the harness's external reach.  Unit: a profile.  Two opposite verdicts live here and both
    are reported: where NO profile is in the window the verdict is an ABSENCE (reversed by one
    profile), and where profiles ARE in the window it is an effect (reversed by their leaving)."""
    pub = ext["anchor_published_numbers"]
    lo = pub["worst_trace_degradation"]
    out = {}
    for p, rows in ext["cells"].items():
        inw = [r["profile"] for r in rows if r["worst_unit_degradation"] >= lo]
        best = max(r["worst_unit_degradation"] for r in rows)
        out[p] = {
            "unit": "profile (%d of them)" % len(rows),
            "asserts": "an effect (the harness reaches the published scale)" if inw
                       else "an ABSENCE (no profile reaches the published scale)",
            "rule": "a profile reaches the published robustness scale (%.3f)" % lo,
            "value": {"in_window": len(inw), "profiles": len(rows)},
            "k_inversions": len(inw) if inw else None,
            "distance_to_boundary": None if inw else round(lo - best, 6),
            "distance_rule": None if inw else
                             "the best profile sits this far BELOW the published scale (in worst-unit "
                             "degradation); only a better profile crosses it",
            "kind": "exact (a threshold count over the recorded profiles)",
        }
    return out


def null_shift_bound(suf):
    """L2 -- the specificity control: a scope LIMIT, and the stage records one aggregate per problem
    with no unit breakdown, so no bound in units can be derived.  Reported as not derivable."""
    ns = suf["null_shift_from_the_even_target_adv_over_mde"]
    return {p: {"unit": "not derivable: the stage records one aggregate per problem",
                "asserts": "an ABSENCE (the design does not favour its own odd term under a sign-free "
                           "target)",
                "rule": "the advantage over MDE under the EVEN synthetic target is negative",
                "value": v, "k_inversions": None,
                "distance_to_boundary": abs(v),
                "distance_rule": "the aggregate sits this many MDEs below zero",
                "kind": "the margin is exact; NO bound in units is derivable, because the per-unit rows "
                        "behind the aggregate are not recorded -- stated as such rather than estimated "
                        "into a number"}
            for p, v in ns.items()}


def compute():
    suf, ext = load(SUF), load(EXT)
    return {
        "schema": 1,
        "note": ("criterion (d)'s flip-count bound, computed from the committed stage artefacts. The "
                 "unit is the smallest observation the producing stage records and the bound is the "
                 "FEWEST unit inversions that could reverse the number's verdict (inversions applied "
                 "strongest-support-first). A verdict that asserts an ABSENCE has no inversion bound: "
                 "it is reversed by MORE support, so its margin is reported as a distance to the "
                 "decision boundary instead. `kind` marks exact bounds apart from estimates under a "
                 "stated assumption."),
        "F1_1_witness": witness_bound(suf),
        "F1_2_sign_channel": contrast_bound(suf),
        "F1_3_ordering": ordering_bound(ext),
        "L2_null_shift": null_shift_bound(suf),
        "L3_reach": reach_bound(ext),
    }


def selftest():
    """The bound's own behaviour, planted in both directions -- a bound that cannot be wrong is not a
    bound, and the direction rule (effect vs absence) is exactly what the first cut got wrong."""
    bad = 0

    def check(label, ok, extra=""):
        nonlocal bad
        bad += 0 if ok else 1
        print("%-4s %s%s" % ("PASS" if ok else "FAIL", label, (" -- " + str(extra)) if extra else ""))

    # count rule, both directions
    flags = [True] * 31 + [False] * 8
    k = min_inversions_count(flags, 20)
    check("count rule: 31 of 39 supporting, majority rule needs 20 -> k=12", k == 12, k)
    check("count rule, planted: exactly 20 supporting (the threshold) -> k=1",
          min_inversions_count([True] * 20 + [False] * 19, 20) == 1)
    check("count rule, planted: already failing (19 supporting) -> k=0",
          min_inversions_count([True] * 19 + [False] * 20, 20) == 0)

    # interval rule, both directions, on a verdict that asserts an effect
    strong = [-0.1 - 0.01 * i for i in range(39)]        # every block strongly negative
    k = min_inversions_interval(strong, lambda v: -v)
    xs = list(strong)
    order = sorted(range(len(xs)), key=lambda i: -abs(xs[i]))
    for j in range(k - 1):
        xs[order[j]] = -xs[order[j]]
    # after k-1 inversions the verdict must STILL hold -- otherwise the sweep was not minimal and
    # the "k" it printed is not the fewest changes (the first version of this check asserted the
    # opposite and failed on a correct sweep: the test, not the code, was wrong)
    check("interval rule: k inversions reverse it, and k-1 leave it standing",
          k > 0 and interval_excludes_zero(xs), "k=%d, interval after k-1=%s"
          % (k, [round(v, 4) for v in t_interval(xs)]))
    check("interval rule, planted: an interval already containing 0 -> k=0",
          min_inversions_interval([-0.1, 0.1], lambda v: -v) == 0)
    # a verdict no inversion can reverse: the mirror of a positive value is itself (invert = identity)
    check("interval rule, planted: a verdict no inversion reverses -> the sweep exhausts and says so",
          min_inversions_interval([0.1] * 39, lambda v: v) > len([0.1] * 39))

    # the direction rule: an ABSENCE verdict must carry no inversion bound and a distance instead
    js = compute()
    absence = [v for v in js["F1_2_sign_channel"].values() if v["asserts"].startswith("an ABSENCE")]
    ok = absence and all(v["k_inversions"] is None and v["distance_to_boundary"] > 0 for v in absence)
    check("an ABSENCE verdict carries no inversion bound and a positive distance", bool(ok),
          [(v["value"]["advantage_vs_mde"], v["distance_to_boundary"]) for v in absence])
    effect = [v for v in js["F1_2_sign_channel"].values() if v["asserts"] == "an effect"]
    check("an EFFECT verdict carries an inversion bound",
          all(isinstance(v["k_inversions"], int) and v["k_inversions"] > 0 for v in effect),
          [(v["value"]["advantage_vs_mde"], v["k_inversions"]) for v in effect])

    # the identity leg must be reported as having no bound at all
    w = js["F1_1_witness"]
    check("the witness's identity leg is reported as having no flip bound", "no flip bound" in w["note"])
    check("the witness's binding leg is the smaller of its two legs",
          w["k_inversions"] == min(w["legs"]["count"]["k_inversions"], w["legs"]["interval"]["k_inversions"]))

    # and the numbers the manuscript will quote must be the numbers this file writes
    on_disk = json.load(io.open(OUT, encoding="utf-8")) if os.path.exists(OUT) else None
    check("the artefact on disk agrees with a fresh computation (%s)" % ("present" if on_disk else "absent"),
          on_disk is None or on_disk == js)
    print("selftest: %d case(s) failed" % bad)
    return 1 if bad else 0


def main():
    js = compute()
    io.open(OUT, "w", encoding="utf-8").write(json.dumps(js, indent=1, ensure_ascii=False) + "\n")
    w = js["F1_1_witness"]
    print("flip bound -- FEWEST unit inversions that could reverse each headline verdict")
    print("F1.1 witness  count leg (%s): %s -> k=%d"
          % (w["legs"]["count"]["rule"], w["legs"]["count"]["value"], w["legs"]["count"]["k_inversions"]))
    print("F1.1 witness  interval leg (%s): %s -> k=%d"
          % (w["legs"]["interval"]["rule"], w["legs"]["interval"]["value"],
             w["legs"]["interval"]["k_inversions"]))
    print("F1.1 witness  binding: %s, k=%d block unit(s); %s"
          % (w["binding_leg"], w["k_inversions"], w["paired_observations_per_inverted_block"]))
    for p, v in sorted(js["F1_2_sign_channel"].items()):
        if v["k_inversions"] is None:
            print("F1.2 %-7s ABSENCE verdict: no inversion bound; distance to the bar %.4f MDE(s)"
                  % (p, v["distance_to_boundary"]))
        else:
            print("F1.2 %-7s k=%d cluster(s) via %s (%s)"
                  % (p, v["k_inversions"], v["binding_leg"], "estimate"))
    for p, v in sorted(js["F1_3_ordering"].items()):
        print("F1.3 %-7s tau=%.4f over %d pairs -> k=%d pair inversion(s)"
              % (p, v["value"]["tau"], v["value"]["pairs"], v["k_inversions"]))
    for p, v in sorted(js["L3_reach"].items()):
        if v["k_inversions"] is None:
            print("L3   %-7s no profile in window -> distance to the scale %.4f"
                  % (p, v["distance_to_boundary"]))
        else:
            print("L3   %-7s %d/%d in window -> k=%d (all of them must leave)"
                  % (p, v["value"]["in_window"], v["value"]["profiles"], v["k_inversions"]))
    print("L2   null shift: margin exact, no bound in units derivable (per-unit rows not recorded)")
    return 0


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        raise SystemExit(selftest())
    raise SystemExit(main())
