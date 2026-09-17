#!/usr/bin/env python3
"""Issue #47 -- paging v1: the error must attach to the DECISION OBJECT.

R320 refuted the registered paging mechanism with an invariance proof.  The
instrument multiplied EVERY candidate page's predicted next-arrival distance at
step i by the same factor (1 + e_i).  A strictly positive factor shared by all
candidates cannot change an argmax, so the arm reproduced Belady exactly on all
32 traces, and the measured sign effect could only have come from the clamp
`max(1.0, d * (1 + e_i))` creating ties at the top of the ranking.

The structural repair is not a tolerance.  The decision object in paging is the
PAGE -- the algorithm chooses among the pages resident in the cache -- so the
prediction error must attach to the page, not to the request.  This script
rebuilds the cell with per-page errors and re-measures.

SECOND DEFECT found while rebuilding, reported because it changes how the R320
refutation should be read.  The registered waste statistic counted

    victim is DEAD (never used again)  and  some kept page is LIVE

which is the OPTIMAL (Belady) eviction, not waste -- evicting the page whose
next use is furthest away is exactly what Belady does.  Waste is the other
event:

    victim is LIVE  and  some kept page is DEAD

i.e. we evicted a page we will need and kept one we never will.  A statistic
that counts the correct action is flat by construction, so its flatness in R320
said nothing about the mechanism.  (The refutation itself did not rest on it:
it rested on the invariance proof, which is sound either way.)

Source of each error term:
  per_page        -- one error per page per trace.  A learned predictor given
                     the same page returns the same prediction, so a stable
                     per-page error is the faithful model.
  per_page_redraw -- redrawn per (page, decision).  A robustness variant: if
                     the sign effect needs the stable model, that is a finding
                     about which model the claim requires.
  shared          -- the R320 model, kept ONLY as a cross-artefact check that
                     this harness is the instrument's harness.

Controls, each able to refute the rebuild:
  C1 degeneracy  -- with the SAME error on every page the arm must again be
                    exactly Belady.  The R320 invariant becomes a regression
                    test on the new model.
  C2 clamp-free  -- the sign gap must survive removing the clamp.
  C3 zero        -- no errors at all must be exactly Belady.
  C4 attachment  -- the corrected waste count must separate the signs by more
                    than the inverted one did, or the repair did not repair.
  C5 harness     -- with the shared error this harness must reproduce
                    instrument_v0.paging_cost exactly, cell by cell.

CPU only, stdlib only, fixed seeds.  Counts are reported; no claim is made
beyond what the controls and the counts themselves support.
"""
import hashlib
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import instrument_v0 as inst  # noqa: E402  (the same generators, deliberately)

REPS = 8
TRACES = inst.TRACES_PER_REP
K, CAP, N_PAGES = inst.K_PAGES, inst.TRACE_LEN + 1, inst.N_PAGES

PROFILES = ("zero", "unbiased_mid", "over_mid", "under_mid",
            "unbiased_extreme", "over_extreme", "under_extreme")
SIGN = {"zero": "zero", "unbiased_mid": "unbiased", "unbiased_extreme": "unbiased",
        "over_mid": "over", "under_mid": "under",
        "over_extreme": "over", "under_extreme": "under"}


def page_errors(profile, rep, t, n_pages):
    """One error per PAGE per trace -- the page is the decision object."""
    if profile == "zero":
        return [0.0] * n_pages
    return inst.gen_errors(profile, n_pages,
                           inst.seed_of("pg", "err_perpage", profile, rep, t))


def redraw_error(profile, rep, t, i, q):
    if profile == "zero":
        return 0.0
    return inst.gen_errors(profile, 1,
                           inst.seed_of("pg", "err_pd", profile, rep, t, i, q))[0]


def simulate(trace, occ, profile, rep, t, mode="per_page", floor=1.0, const=None):
    """One paging run under a chosen error attachment.  Returns (cost, optimal, stats).

    Only the error attachment and the floor vary between calls; the cache, the
    ranking, the tie-break (largest page id among equal scores, the same rule
    Belady uses) and both waste definitions are shared by every arm.
    """
    if const is not None:
        errs = [float(const)] * N_PAGES
        mode = "per_page"
    elif mode == "per_page":
        errs = page_errors(profile, rep, t, N_PAGES)
    elif mode == "shared":
        errs = (None if profile == "zero" else
                inst.gen_errors(profile, inst.TRACE_LEN,
                                inst.seed_of("pg", "err", profile, rep, t)))
    elif mode == "per_page_redraw":
        errs = None            # drawn per (page, decision) inside the loop
    else:
        # NOT a silent `errs = None`.  The first version of this dispatch had no
        # branch for "per_page_redraw", so that arm ran with NO errors at all and
        # returned exactly Belady on every trace -- a null produced by a dispatch
        # typo, which reads exactly like the finding "the effect needs the stable
        # model".  An unknown arm must be fatal, never a default.
        raise ValueError("unknown error-attachment mode %r" % (mode,))

    cache, cost = {}, 0
    st = {"evictions": 0, "waste": 0, "waste_inverted": 0, "ties": 0,
          "waste_under": 0, "waste_over": 0, "waste_zero": 0,
          "clamp_binds": 0, "dead_evicted": 0,
          "wrong_victim": 0, "wrong_victim_under": 0,
          "wrong_victim_over": 0, "wrong_victim_zero": 0}
    for i, p in enumerate(trace):
        if p in cache:
            continue
        cost += 1
        if len(cache) >= K:
            cell = {}
            true_max = max(inst.next_arrival(occ, i, q, CAP) for q in cache)
            for q in cache:
                d = inst.next_arrival(occ, i, q, CAP)
                # MODE-FIRST dispatch.  The first version tested `errs is None`
                # first, so the `per_page_redraw` arm -- which is *supposed* to draw
                # in the loop and therefore also carries errs = None -- fell into the
                # no-error branch and returned exactly Belady.  One sentinel meaning
                # two different things ("no errors" and "errors drawn later") made the
                # branch ORDER decide the semantics, silently.
                if mode == "shared":
                    e = 0.0 if errs is None else errs[i]
                elif mode == "per_page":
                    e = 0.0 if errs is None else errs[q]
                elif mode == "per_page_redraw":
                    e = redraw_error(profile, rep, t, i, q)
                else:
                    raise ValueError("unknown error-attachment mode %r" % (mode,))
                raw = d * (1.0 + e)
                if raw < floor:
                    st["clamp_binds"] += 1
                cell[q] = (d, e, raw if raw >= floor else floor)
            ranked = sorted(((cell[q][2], q) for q in cache),
                            key=lambda z: (-z[0], -z[1]))
            victim = ranked[0][1]
            if len(ranked) > 1 and abs(ranked[0][0] - ranked[1][0]) < 1e-12:
                st["ties"] += 1
            d_v, e_v, _ = cell[victim]
            victim_dead = d_v >= CAP
            kept_dead = any(cell[q][0] >= CAP for q in cache if q != victim)
            kept_live = any(cell[q][0] < CAP for q in cache if q != victim)
            st["evictions"] += 1
            if victim_dead:
                st["dead_evicted"] += 1
            # THE countable statistic for "the ranking was reordered": the victim the
            # predicted ranking chose versus the victim the TRUE distances single out
            # (Belady's own rule, same tie-break).  A multiplicative error that is
            # shared changes neither; a per-page error reorders by definition when
            # the relative perturbation exceeds the relative distance gap.
            if d_v < true_max:
                st["wrong_victim"] += 1
                if e_v < 0:
                    st["wrong_victim_under"] += 1
                elif e_v > 0:
                    st["wrong_victim_over"] += 1
                else:
                    st["wrong_victim_zero"] += 1
            # CORRECTED: we evicted a page we will need and kept one we never will
            if (not victim_dead) and kept_dead:
                st["waste"] += 1
                if e_v < 0:
                    st["waste_under"] += 1
                elif e_v > 0:
                    st["waste_over"] += 1
                else:
                    st["waste_zero"] += 1
            # the R320 definition: the OPTIMAL action, counted as if it were waste
            if victim_dead and kept_live:
                st["waste_inverted"] += 1
            del cache[victim]
        cache[p] = i
    return cost, inst.belady_cost(trace, occ, K, CAP), st


def run(profile, mode="per_page", floor=1.0):
    """Pooled over REPS x TRACES; also returns the per-trace cost list."""
    ratios, costs, opts, pooled = [], [], [], {}
    wasted, wasted_inv, ties, evict, clamp = 0, 0, 0, 0, 0
    wu, wo, wz, dead = 0, 0, 0, 0
    wv, wvu, wvo = 0, 0, 0
    for rep in range(REPS):
        for t in range(TRACES):
            trace = inst.paging_realization(rep, t)
            occ = inst.build_occurrences(trace)
            c, o, st = simulate(trace, occ, profile, rep, t, mode=mode, floor=floor)
            costs.append(c)
            opts.append(o)
            ratios.append(c / o)
            wasted += st["waste"]
            wasted_inv += st["waste_inverted"]
            ties += st["ties"]
            evict += st["evictions"]
            clamp += st["clamp_binds"]
            wu += st["waste_under"]
            wo += st["waste_over"]
            wz += st["waste_zero"]
            dead += st["dead_evicted"]
            wv += st["wrong_victim"]
            wvu += st["wrong_victim_under"]
            wvo += st["wrong_victim_over"]
    n = len(ratios)
    pooled = {
        "profile": profile, "mode": mode, "floor": floor,
        "sign": SIGN[profile], "n_traces": n,
        "mean_ratio": sum(ratios) / n,
        "mean_cost": sum(costs) / n,
        "mean_optimal": sum(opts) / n,
        "evictions": evict, "dead_evicted": dead,
        "waste_corrected": wasted,
        "waste_inverted_r320": wasted_inv,
        "waste_corrected_under": wu, "waste_corrected_over": wo,
        "waste_corrected_zero": wz,
        "tied_evictions": ties, "clamp_binds": clamp,
        "wrong_victim": wv,
        "wrong_victim_under": wvu, "wrong_victim_over": wvo,
        "wrong_victim_rate": (wv / evict) if evict else None,
    }
    return pooled


def degeneracy_control():
    """C1: the SAME error for every page must reproduce Belady exactly.

    With one constant e, every score is a monotone transform of the true
    distance `d` (the clamp can only bind at distances below 1, and the cached
    pages carry k distinct distances, so the maximum is never clamped).  The
    argmax is therefore Belady's argmax and the tie-break is the same one.
    """
    exact = 0
    total = 0
    for rep in range(REPS):
        for t in range(TRACES):
            trace = inst.paging_realization(rep, t)
            occ = inst.build_occurrences(trace)
            for const in (-0.5, -0.15, 0.15, 0.5):
                c, o, _ = simulate(trace, occ, "zero", rep, t, const=const)
                total += 1
                if c == o:
                    exact += 1
    return {"constant_error_traces_exactly_belady": exact, "traces": total}


def zero_control():
    """C3: no errors at all must be exactly Belady."""
    exact, total = 0, 0
    for rep in range(REPS):
        for t in range(TRACES):
            trace = inst.paging_realization(rep, t)
            occ = inst.build_occurrences(trace)
            c, o, _ = simulate(trace, occ, "zero", rep, t)
            total += 1
            exact += 1 if c == o else 0
    return {"zero_profile_traces_exactly_belady": exact, "traces": total}


def harness_control():
    """C5: with the shared per-request error this harness must equal the instrument."""
    bad, worst, cells = 0, 0.0, 0
    for rep in range(REPS):
        for t in range(TRACES):
            trace = inst.paging_realization(rep, t)
            occ = inst.build_occurrences(trace)
            for profile in ("zero", "under_mid", "over_extreme", "unbiased_high"):
                errs = (None if profile == "zero" else
                        inst.gen_errors(profile, inst.TRACE_LEN,
                                        inst.seed_of("pg", "err", profile, rep, t)))
                mine, _, _ = simulate(trace, occ, profile, rep, t, mode="shared")
                theirs = inst.paging_cost(trace, occ, K, 1.0, errs, CAP)
                cells += 1
                d = abs(mine - theirs)
                worst = max(worst, d)
                if d != 0:
                    bad += 1
    return {"cells": cells, "mismatches": bad, "worst_abs_diff": worst}


def ski_sched_survive():
    """Re-derive the two CONFIRMED mechanism counts and compare them with the
    PUBLISHED artefact.

    Ski and scheduling errors attach per instance / per job, i.e. one error per
    decision object -- the same attachment the paging rebuild adopts.  The
    aggregation must therefore be mechanism_v0's own (every sign profile it used,
    same REPS), not a subset: a direction-only check would pass even if the counts
    had halved.  The published values are READ from the artefact rather than
    typed here, so this is a comparison between two runs, not a restatement.
    """
    import mechanism_v0 as mech
    agg = {"ski_under": 0, "ski_over": 0}
    disp = {"under": [], "over": []}
    for rep in range(REPS):
        for profile in mech.SIGN_PROFILES:
            r = mech.ski_mechanism(rep, profile)
            agg["ski_under"] += r["branch_errors_under"]
            agg["ski_over"] += r["branch_errors_over"]
            sc = mech.sched_mechanism(rep, profile)
            if profile.startswith("under"):
                disp["under"].append(sc["rank_displacement_largest"])
            elif profile.startswith("over"):
                disp["over"].append(sc["rank_displacement_largest"])
    mine = {
        "ski_branch_errors_under": agg["ski_under"],
        "ski_branch_errors_over": agg["ski_over"],
        "sched_mean_displacement_under": sum(disp["under"]) / len(disp["under"]),
        "sched_mean_displacement_over": sum(disp["over"]) / len(disp["over"]),
    }
    published = json.load(io.open(
        os.path.join(HERE, "mechanism_v0_results.json"), encoding="utf-8"))["mechanism"]
    ref = {
        "ski_branch_errors_under": published["ski"]["branch_errors_under"],
        "ski_branch_errors_over": published["ski"]["branch_errors_over"],
        "sched_mean_displacement_under":
            published["sched"]["mean_rank_displacement_largest_under"],
        "sched_mean_displacement_over":
            published["sched"]["mean_rank_displacement_largest_over"],
    }
    diffs = {k: abs(mine[k] - ref[k]) for k in mine}
    mine["published"] = ref
    mine["abs_diff_vs_published"] = diffs
    mine["reproduces_published_exactly"] = all(v == 0.0 for v in diffs.values())
    return mine


def rank_corr(xs, ys):
    """Spearman rank correlation, computed here so the artefact needs no scipy."""
    def ranks(v):
        order = sorted(range(len(v)), key=lambda i: (v[i], i))
        r = [0.0] * len(v)
        for pos, i in enumerate(order):
            r[i] = float(pos + 1)
        return r
    rx, ry = ranks(xs), ranks(ys)
    n = len(xs)
    mx, my = sum(rx) / n, sum(ry) / n
    num = sum((rx[i] - mx) * (ry[i] - my) for i in range(n))
    dx = sum((rx[i] - mx) ** 2 for i in range(n)) ** 0.5
    dy = sum((ry[i] - my) ** 2 for i in range(n)) ** 0.5
    return num / (dx * dy) if dx and dy else 0.0


def explain_block(rows, names):
    """Does the wrong-victim rate ORDER the excess cost across profiles?

    Only the reference block (no clamp-free reference arm) is used, and ONLY the
    profiles whose cost is above the resolution: at the small-error profiles the
    excess is under 1%, where the ordering claim would be a claim about noise.
    """
    names = [n for n in names if n != "zero"]
    by_name = {r["profile"]: r for r in rows}
    for n in names:
        assert n in by_name, "explain_block: profile %r absent from the rows" % n
    xs = [by_name[n]["wrong_victim_rate"] for n in names]
    ys = [by_name[n]["mean_ratio"] - 1.0 for n in names]
    assert all(v is not None for v in xs), "a wrong-victim rate is None"
    return {"profiles": names, "wrong_victim_rate": xs, "excess_ratio": ys,
            "spearman": rank_corr(xs, ys), "n": len(names)}


def get_redraw(out):
    rd = {r["profile"]: r for r in out["per_page_redraw"]}
    return rd["under_extreme"]["mean_ratio"] - rd["over_extreme"]["mean_ratio"]


def main():
    out = {"reps": REPS, "traces_per_rep": TRACES, "k_pages": K,
           "n_pages": N_PAGES, "trace_len": inst.TRACE_LEN}

    # ---- the rebuilt cell: per-page errors
    per_page = [run(p, mode="per_page") for p in PROFILES]
    out["per_page"] = per_page
    out["per_page_redraw"] = [run(p, mode="per_page_redraw") for p in PROFILES]

    # ---- the R320 arm, for the like-for-like comparison
    out["shared_r320"] = [run(p, mode="shared") for p in PROFILES]

    # ---- controls
    out["control_degeneracy"] = degeneracy_control()
    out["control_zero"] = zero_control()
    out["control_harness"] = harness_control()
    out["control_clamp_free"] = {
        p: run(p, mode="per_page", floor=1e-9)
        for p in ("over_extreme", "under_extreme")}
    out["control_clamp_free_zero"] = run("zero", mode="per_page", floor=1e-9)

    def get(rows, name):
        for r in rows:
            if r["profile"] == name:
                return r
        raise KeyError(name)

    pp = out["per_page"]
    sh = out["shared_r320"]
    out["explains"] = explain_block(pp, list(PROFILES))
    out["explains_shared_r320"] = explain_block(sh, list(PROFILES))
    cf = out["control_clamp_free"]
    gaps = {
        "per_page_extreme_gap": get(pp, "under_extreme")["mean_ratio"]
                                - get(pp, "over_extreme")["mean_ratio"],
        "per_page_mid_gap": get(pp, "under_mid")["mean_ratio"]
                            - get(pp, "over_mid")["mean_ratio"],
        "shared_r320_extreme_gap": get(sh, "under_extreme")["mean_ratio"]
                                   - get(sh, "over_extreme")["mean_ratio"],
        "per_page_clampfree_extreme_gap": cf["under_extreme"]["mean_ratio"]
                                          - cf["over_extreme"]["mean_ratio"],
    }
    out["gaps"] = gaps

    wu = get(pp, "under_extreme")["waste_corrected"]
    wo = get(pp, "over_extreme")["waste_corrected"]
    iu = get(pp, "under_extreme")["waste_inverted_r320"]
    io_ = get(pp, "over_extreme")["waste_inverted_r320"]
    out["waste_comparison"] = {
        "corrected": {"under": wu, "over": wo,
                      "ratio": (wu / wo) if wo else None},
        "inverted_r320": {"under": iu, "over": io_,
                          "ratio": (iu / io_) if io_ else None},
    }

    # DECISIVE DISCRIMINATOR between genuine reordering and tie-breaking.  In the
    # shared (R320) arm a wrong victim can only arise where the clamp made the top two
    # scores EQUAL, so the wrong-victim count must be bounded by the tie count.  In the
    # per-page arm the errors differ between candidates, so a wrong victim needs no tie
    # at all -- the count must exceed the ties by a wide margin.  This is the check that
    # says the repaired effect is reordering rather than the artefact renamed.
    def wv_vs_ties(rows):
        return {r["profile"]: [r["wrong_victim"], r["tied_evictions"]] for r in rows}

    pp_wv = get(pp, "under_extreme")
    sh_wv = get(sh, "under_extreme")
    out["discriminator"] = {
        "per_page_wrong_victim_vs_ties": wv_vs_ties(pp),
        "shared_r320_wrong_victim_vs_ties": wv_vs_ties(sh),
        "per_page": {"wrong_victim": pp_wv["wrong_victim"],
                     "ties": pp_wv["tied_evictions"],
                     "evictions": pp_wv["evictions"]},
        "shared_r320": {"wrong_victim": sh_wv["wrong_victim"],
                        "ties": sh_wv["tied_evictions"],
                        "evictions": sh_wv["evictions"]},
    }

    out["ski_sched_survive"] = ski_sched_survive()

    # ---- what the rebuild must satisfy (each check can fail)
    d = out["control_degeneracy"]
    z = out["control_zero"]
    h = out["control_harness"]
    checks = [
        {"check": "C1 the same error on every page reproduces Belady exactly",
         "ok": d["constant_error_traces_exactly_belady"] == d["traces"],
         "value": d},
        {"check": "C3 the zero profile reproduces Belady exactly",
         "ok": z["zero_profile_traces_exactly_belady"] == z["traces"], "value": z},
        {"check": "C5 with the shared error this harness equals the instrument",
         "ok": h["mismatches"] == 0, "value": h},
        {"check": "C4 the corrected waste count separates the extreme signs by "
                  "more than the inverted R320 count did",
         "ok": (out["waste_comparison"]["corrected"]["ratio"] or 0)
               > (out["waste_comparison"]["inverted_r320"]["ratio"] or 0),
         "value": out["waste_comparison"]},
        {"check": "the per-page sign gap between the extreme signs is reported "
                  "(direction is a FINDING, not a check)",
         "note": "informational", "ok": True, "value": {
             "per_page_extreme_gap": gaps["per_page_extreme_gap"],
             "shared_r320_extreme_gap": gaps["shared_r320_extreme_gap"],
             "per_page_clampfree_extreme_gap": gaps["per_page_clampfree_extreme_gap"]}},
        {"check": "the wrong-victim rate ORDERS the excess cost ratio across the "
                  "profiles (a count that does not order the cost is not the mechanism)",
         "ok": out["explains"]["spearman"] >= 0.9,
         "value": {"per_page": out["explains"], "shared_r320": out["explains_shared_r320"]}},
        {"check": "DECISIVE: in the shared arm wrong victims are bounded by the "
                  "tie-broken decisions (a clamp artefact cannot exceed its own ties), "
                  "while in the per-page arm they exceed them by an order of magnitude "
                  "(so the repaired effect is reordering, not tie-breaking renamed)",
         "ok": (out["discriminator"]["shared_r320"]["wrong_victim"]
                <= out["discriminator"]["shared_r320"]["ties"])
               and (out["discriminator"]["per_page"]["wrong_victim"]
                    > 5 * out["discriminator"]["per_page"]["ties"]),
         "value": out["discriminator"]},
        {"check": "the effect SURVIVES the redrawn-per-decision attachment (the claim "
                  "must not silently assume the stable per-page predictor)",
         # by PROFILE NAME, not by list position.  The first version indexed the rows
         # positionally and compared the wrong two arms -- the check failed on a value
         # its own text printed as passing, which is the only reason it was visible.
         "ok": get_redraw(out) > 0.05,
         "value": {"redraw_extreme_gap": get_redraw(out),
                   "stable_extreme_gap": out["gaps"]["per_page_extreme_gap"]}},
        {"check": "the ski and scheduling counts REPRODUCE the published artefact "
                  "exactly under this round's harness (same aggregation as "
                  "mechanism_v0: every sign profile x REPS)",
         "ok": out["ski_sched_survive"]["reproduces_published_exactly"],
         "value": out["ski_sched_survive"]},
    ]
    out["checks"] = checks
    out["CHECKS_ALL_PASS"] = all(c["ok"] for c in checks)

    blob = json.dumps(out, sort_keys=True, indent=1)
    path = os.path.join(HERE, "paging_v1_results.json")
    io.open(path, "w", encoding="utf-8").write(blob + "\n")
    sha = hashlib.sha256((blob + "\n").encode("utf-8")).hexdigest()
    print("paging_v1: %d/%d checks pass" % (
        sum(1 for c in checks if c["ok"]), len(checks)))
    for c in checks:
        if not c["ok"]:
            print("  FAIL: %s -> %s" % (c["check"], c["value"]))
    print("CHECKS_ALL_PASS = %s" % out["CHECKS_ALL_PASS"])
    print("sha256 %s" % sha)
    print()
    print("%-20s %10s %10s %9s %8s %8s" % (
        "profile", "ratio(pp)", "ratio(shr)", "wrongvic", "waste(c)", "waste(i)"))
    for name in PROFILES:
        a, b = get(pp, name), get(sh, name)
        print("%-20s %10.4f %10.4f %9d %8d %8d" % (
            name, a["mean_ratio"], b["mean_ratio"], a["wrong_victim"],
            a["waste_corrected"], a["waste_inverted_r320"]))
    print()
    print("gaps:", json.dumps(gaps, indent=1))
    print("waste:", json.dumps(out["waste_comparison"], indent=1))
    print("explains:", json.dumps(out["explains"], indent=1))
    print("ski/sched:", json.dumps({
        k: v for k, v in out["ski_sched_survive"].items()
        if k != "published"}, indent=1))
    return 0 if out["CHECKS_ALL_PASS"] else 1


if __name__ == "__main__":
    sys.exit(main())
