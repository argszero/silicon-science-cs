#!/usr/bin/env python3
"""Issue #47 -- mechanism v0: turn the three boundary hypotheses into COUNTS.

The scorer found the sign effect but could not say *why*.  §11 registered three
hypotheses, all of the same shape: the priced sign is set by which branch the
decision takes at the boundary, not by the error magnitude.  Each is now a
countable statistic:

  ski rental  -- an under-predicted horizon drops the trusted arm into the
      `never buy` branch while the offline optimum is `buy`: the instance pays
      n*r where the optimum is b.  Counted as the number of instances where the
      trusted action differs from the offline-optimal action, split by sign.
  paging      -- a page never used again carries the cap distance; an
      under-predicted distance can pull such a page below an ordinary page's and
      evict it while a page that WILL be used again is kept.  Counted as the
      number of evictions that remove a never-again page while some retained
      page is used again later ("wasted evictions"), split by sign.
  scheduling  -- an under-predicted long job looks short, is scheduled early,
      and total flow time counts an early job n times.  Counted as the mean rank
      displacement of the largest job, split by sign.

CRITICAL DESIGN POINT: this script IMPORTS instrument_v0 and reuses its
realization / error / coin generators, so the counts and the ratio measurements
describe the same instances.  A count that explained a different draw would be
worthless, so the script also re-derives the lambda=1 cell means and asserts they
equal the instrument's -- a cross-artefact consistency check, not an assertion.

CPU only, stdlib only, fixed seeds.  Counts are reported; no claim is made beyond
what the consistency check and the counts themselves support.
"""
import io, json, math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import instrument_v0 as inst  # noqa: E402  (the same generators, deliberately)

REPS = 8
SIGN_PROFILES = ("zero", "over_mid", "under_mid", "over_extreme", "under_extreme")


def sign_of(mu):
    return "over" if mu > 0 else ("under" if mu < 0 else "zero")


# =============================================================== ski rental
def ski_mechanism(rep, profile):
    ns = inst.ski_realization(rep)
    errs = inst.gen_errors(profile, len(ns), inst.seed_of("ski", "err", profile, rep))
    coins = inst.ski_coins(rep)
    r, b = inst.SKI_R, inst.SKI_B
    trusted_cost, robust_cost = [], []
    branch_error_under, branch_error_over, zero_err = 0, 0, 0
    excess_under, excess_over = [], []
    for i, n in enumerate(ns):
        n_hat = max(1, int(round(n * (1.0 + errs[i]))))
        # the two arms' costs on this instance (lambda=1 takes the trusted one)
        d_trusted = inst.ski_trusted_day(n_hat)
        c_trusted = inst.ski_cost(d_trusted, n)
        c_robust = inst.ski_cost(inst.ski_classic_day(), n)
        c_opt = inst.ski_offline(n)
        trusted_cost.append(c_trusted)
        robust_cost.append(c_robust)
        # the offline-optimal ACTION: buy iff buying is no worse than never buying
        optimal_branch_is_buy = (b <= n * r)
        trusted_branch_is_buy = (d_trusted == 1)
        e = errs[i]
        if e == 0:
            zero_err += 1
        if trusted_branch_is_buy != optimal_branch_is_buy:
            if e < 0:
                branch_error_under += 1
                excess_under.append(c_trusted - c_opt)
            elif e > 0:
                branch_error_over += 1
                excess_over.append(c_trusted - c_opt)
    m = len(ns)
    return {
        "problem": "ski", "rep": rep, "profile": profile, "n_instances": m,
        "mean_ratio_trusted": sum(c / inst.ski_offline(n) for c, n in zip(trusted_cost, ns)) / m,
        "mean_cost_trusted": sum(trusted_cost) / m,
        "mean_cost_robust": sum(robust_cost) / m,
        "branch_errors_under": branch_error_under,
        "branch_errors_over": branch_error_over,
        "mean_excess_cost_under": (sum(excess_under) / len(excess_under)) if excess_under else 0.0,
        "mean_excess_cost_over": (sum(excess_over) / len(excess_over)) if excess_over else 0.0,
    }


# =================================================================== paging
def paging_mechanism(rep, profile, t):
    trace = inst.paging_realization(rep, t)
    occ = inst.build_occurrences(trace)
    k, L = inst.K_PAGES, inst.TRACE_LEN
    cap = L + 1
    errs = (None if profile == "zero"
            else inst.gen_errors(profile, L, inst.seed_of("pg", "err", profile, rep, t)))
    cache, staleness, cost = {}, {}, 0
    evictions = wasted = ties = ties_under = ties_over = 0
    wasted_under = wasted_over = 0
    for i, p in enumerate(trace):
        if p in cache:
            for q in staleness:
                staleness[q] += 1
            staleness[p] = 0
            continue
        cost += 1
        if len(cache) >= k:
            e = errs[i] if errs is not None else 0.0
            lam_score = 1.0   # lambda=1 arm: evict the largest predicted next-arrival

            def score(q):
                d = inst.next_arrival(occ, i, q, cap)
                if errs is not None:
                    d = max(1.0, d * (1.0 + e))
                return lam_score * d + (1.0 - lam_score) * staleness[q]

            ranked = sorted(((score(q), q) for q in cache), key=lambda t: (-t[0], -t[1]))
            victim = ranked[0][1]
            # an eviction whose top score is TIED is decided by the index tie-break,
            # i.e. with no information: the signal the blend was supposed to carry has
            # been destroyed.  The floor max(1.0, d*(1+e)) is the suspected cause --
            # it saturates distances under a negative error and leaves them distinct
            # under a positive one (a multiplicative error alone cannot change the
            # argmax, so any sign effect must come from this clamping).
            tied = (len(ranked) > 1 and abs(ranked[0][0] - ranked[1][0]) < 1e-12)
            if tied:
                ties += 1
                if e < 0:
                    ties_under += 1
                elif e > 0:
                    ties_over += 1
            # was the eviction wasted?  victim never used again, while some page we
            # KEEP will be used again -> we evicted a dead page in hand for a live one
            victim_dead = inst.next_arrival(occ, i, victim, cap) >= cap
            kept_live = any(inst.next_arrival(occ, i, q, cap) < cap for q in cache if q != victim)
            evictions += 1
            if victim_dead and kept_live:
                wasted += 1
                if e < 0:
                    wasted_under += 1
                elif e > 0:
                    wasted_over += 1
            del cache[victim]
            del staleness[victim]
        cache[p] = i
        for q in staleness:
            staleness[q] += 1
        staleness[p] = 0
    return {
        "problem": "paging", "rep": rep, "profile": profile, "trace": t,
        "cost": cost, "optimal": inst.belady_cost(trace, occ, k, cap),
        "evictions": evictions, "wasted_evictions": wasted,
        "wasted_under": wasted_under, "wasted_over": wasted_over,
        "tied_evictions": ties, "ties_under": ties_under, "ties_over": ties_over,
    }


# =============================================================== scheduling
def sched_mechanism(rep, profile):
    jobs = inst.sched_realization(rep)
    n = len(jobs)
    errs = inst.gen_errors(profile, n, inst.seed_of("sc", "err", profile, rep))
    pred = [max(1, int(round(jobs[j] * (1.0 + errs[j])))) for j in range(n)]
    order = sorted(range(n), key=lambda j: (pred[j], j))          # lambda=1: SPT on prediction
    spt = sorted(range(n), key=lambda j: (jobs[j], j))
    rank_pred = {j: r for r, j in enumerate(order)}
    rank_spt = {j: r for r, j in enumerate(spt)}
    big = max(range(n), key=lambda j: (jobs[j], j))               # the largest job
    displacement = rank_pred[big] - rank_spt[big]                 # >0 = scheduled later than it should be
    disp_all = sum(abs(rank_pred[j] - rank_spt[j]) for j in range(n)) / n
    got = inst.flow_of_order(order, jobs)
    opt = inst.flow_of_order(spt, jobs)
    return {
        "problem": "sched", "rep": rep, "profile": profile, "n_jobs": n,
        "cost": got, "optimal": opt, "ratio": got / opt,
        "largest_job": jobs[big], "rank_displacement_largest": displacement,
        "mean_abs_rank_displacement": disp_all,
        "largest_job_underpredicted": max(1, int(round(jobs[big] * (1.0 + errs[big])))) < jobs[big],
    }


# ==================================================================== driver
def paging_floor_control(rep, profile, t, floor):
    """The tie statistic blames the clamp max(1.0, d*(1+e)).  If the sign effect is a
    property of the ASSERTED GEOMETRY of predicted next-arrival distance, it must
    survive lowering the floor; if it vanishes, the effect was a property of the
    clamp value, i.e. of my implementation, and the manuscript may not present it as
    a property of the problem.  Returns (cost, optimal)."""
    trace = inst.paging_realization(rep, t)
    occ = inst.build_occurrences(trace)
    k, L = inst.K_PAGES, inst.TRACE_LEN
    cap = L + 1
    errs = inst.gen_errors(profile, L, inst.seed_of("pg", "err", profile, rep, t))
    cache, staleness, cost = {}, {}, 0
    for i, p in enumerate(trace):
        if p in cache:
            for q in staleness:
                staleness[q] += 1
            staleness[p] = 0
            continue
        cost += 1
        if len(cache) >= k:
            e = errs[i]

            def score(q):
                return max(floor, inst.next_arrival(occ, i, q, cap) * (1.0 + e))

            victim = max(cache, key=lambda q: (score(q), q))
            del cache[victim]
            del staleness[victim]
        cache[p] = i
        for q in staleness:
            staleness[q] += 1
        staleness[p] = 0
    return cost, inst.belady_cost(trace, occ, k, cap)


def paging_shared_factor_probe(rep, t):
    """Prove the invariance directly.  Score every candidate by
    d_q * exp(e_i) -- a POSITIVE per-request shared factor.  The factor multiplies
    every candidate equally, so the argmax cannot change and the eviction sequence
    must be EXACTLY Belady for every profile, with no clamping to hide behind.
    If the ratio is exactly 1.0, then a shared per-request error carries NO
    information and the sign effect seen in the instrument comes entirely from the
    clamp; if it is not 1.0, the invariance argument is wrong and must be dropped.
    """
    trace = inst.paging_realization(rep, t)
    occ = inst.build_occurrences(trace)
    k, L = inst.K_PAGES, inst.TRACE_LEN
    cap = L + 1
    errs = inst.gen_errors("under_extreme", L, inst.seed_of("pg", "err", "under_extreme", rep, t))
    cache, staleness, cost = {}, {}, 0
    for i, p in enumerate(trace):
        if p in cache:
            for q in staleness:
                staleness[q] += 1
            staleness[p] = 0
            continue
        cost += 1
        if len(cache) >= k:
            factor = math.exp(errs[i])

            def score(q):
                return inst.next_arrival(occ, i, q, cap) * factor

            victim = max(cache, key=lambda q: (score(q), q))
            del cache[victim]
            del staleness[victim]
        cache[p] = i
        for q in staleness:
            staleness[q] += 1
        staleness[p] = 0
    return cost, inst.belady_cost(trace, occ, k, cap)


def main():
    d = json.load(io.open(os.path.join(HERE, "instrument_v0_results.json"), encoding="utf-8"))
    rows = d["rows"]
    index = {(r["problem"], r["profile"], r["replicate"], r["lam"]): r for r in rows}

    recs = {"ski": [], "paging": [], "sched": []}
    for rep in range(REPS):
        for profile in SIGN_PROFILES:
            recs["ski"].append(ski_mechanism(rep, profile))
            for t in range(inst.TRACES_PER_REP):
                recs["paging"].append(paging_mechanism(rep, profile, t))
            recs["sched"].append(sched_mechanism(rep, profile))

    # ------------------------------------------------- consistency (cross-artefact)
    checks = []
    bad = 0
    worst = 0.0
    for r in recs["ski"]:
        ref = index[(("ski"), r["profile"], r["rep"], 1.0)]["mean_ratio"]
        diff = abs(r["mean_ratio_trusted"] - ref)
        worst = max(worst, diff)
        bad += (diff > 1e-12)
    checks.append({"check": "ski: mechanism re-derivation matches the instrument's lambda=1 cell mean",
                   "value": {"mismatches": bad, "worst_abs_diff": worst}, "ok": bad == 0})

    bad = 0
    worst = 0.0
    for r in recs["sched"]:
        ref = index[("sched", r["profile"], r["rep"], 1.0)]["mean_ratio"]
        diff = abs(r["ratio"] - ref)
        worst = max(worst, diff)
        bad += (diff > 1e-12)
    checks.append({"check": "sched: mechanism re-derivation matches the instrument's lambda=1 cell ratio",
                   "value": {"mismatches": bad, "worst_abs_diff": worst}, "ok": bad == 0})

    bad = 0
    for r in recs["paging"]:
        tr = inst.paging_realization(r["rep"], r["trace"])
        occ = inst.build_occurrences(tr)
        # the instrument takes lambda=1 with an ALL-ZERO error array for the "zero"
        # profile (errs is None only at lambda=0) -- an earlier version of this check
        # passed lambda=0 for that profile, so it compared my lambda=1 cost against
        # the LRU cost and failed on exactly the 32 zero-profile traces.
        ref_cost = inst.paging_cost(
            tr, occ, inst.K_PAGES, 1.0,
            inst.gen_errors(r["profile"], inst.TRACE_LEN,
                            inst.seed_of("pg", "err", r["profile"], r["rep"], r["trace"])),
            inst.TRACE_LEN + 1)
        bad += (ref_cost != r["cost"])
    checks.append({"check": "paging: mechanism re-derivation reproduces the instrument's cost exactly",
                   "value": {"mismatches": bad}, "ok": bad == 0})

    # ------------------------------------------- paging clamp control (the artifact test)
    floor_ctrl = {}
    for floor in (1.0, 1e-9):
        for profile in ("over_extreme", "under_extreme"):
            ratios = []
            for rep in range(REPS):
                for t in range(inst.TRACES_PER_REP):
                    c, o = paging_floor_control(rep, profile, t, floor)
                    ratios.append(c / o)
            floor_ctrl["floor=%g/%s" % (floor, profile)] = sum(ratios) / len(ratios)
    gap_1 = floor_ctrl["floor=1/under_extreme"] - floor_ctrl["floor=1/over_extreme"]
    gap_eps = floor_ctrl["floor=1e-09/under_extreme"] - floor_ctrl["floor=1e-09/over_extreme"]

    # ------------------------------------------------------------------- counts
    def agg(problem, key, profile_filter=None):
        tot = 0
        for r in recs[problem]:
            if profile_filter and r["profile"] != profile_filter:
                continue
            tot += r[key]
        return tot

    mech = {
        "ski": {
            "branch_errors_under": agg("ski", "branch_errors_under"),
            "branch_errors_over": agg("ski", "branch_errors_over"),
            "mean_excess_cost_under": sum(r["mean_excess_cost_under"] for r in recs["ski"]
                                          if r["profile"].startswith("under")) / max(1, sum(
                                              1 for r in recs["ski"] if r["profile"].startswith("under"))),
            "mean_excess_cost_over": sum(r["mean_excess_cost_over"] for r in recs["ski"]
                                         if r["profile"].startswith("over")) / max(1, sum(
                                             1 for r in recs["ski"] if r["profile"].startswith("over"))),
        },
        "paging": {
            "evictions": agg("paging", "evictions"),
            "wasted_evictions": agg("paging", "wasted_evictions"),
            "wasted_under": agg("paging", "wasted_under"),
            "wasted_over": agg("paging", "wasted_over"),
            "tied_evictions": agg("paging", "tied_evictions"),
            "ties_under": agg("paging", "ties_under"),
            "ties_over": agg("paging", "ties_over"),
        },
        "sched": {
            "mean_rank_displacement_largest_under": sum(r["rank_displacement_largest"] for r in recs["sched"]
                                                        if r["profile"].startswith("under")) / max(
                1, sum(1 for r in recs["sched"] if r["profile"].startswith("under"))),
            "mean_rank_displacement_largest_over": sum(r["rank_displacement_largest"] for r in recs["sched"]
                                                       if r["profile"].startswith("over")) / max(
                1, sum(1 for r in recs["sched"] if r["profile"].startswith("over"))),
            "mean_abs_rank_displacement_under": sum(r["mean_abs_rank_displacement"] for r in recs["sched"]
                                                    if r["profile"].startswith("under")) / max(
                1, sum(1 for r in recs["sched"] if r["profile"].startswith("under"))),
            "mean_abs_rank_displacement_over": sum(r["mean_abs_rank_displacement"] for r in recs["sched"]
                                                   if r["profile"].startswith("over")) / max(
                1, sum(1 for r in recs["sched"] if r["profile"].startswith("over"))),
        },
    }

    # each mechanism must point the way the measured ratio points: the WORSE sign is
    # the one with the larger boundary-error count / displacement
    checks.append({"check": "ski: more branch errors under under-prediction than over",
                   "value": [mech["ski"]["branch_errors_under"], mech["ski"]["branch_errors_over"]],
                   "ok": mech["ski"]["branch_errors_under"] > mech["ski"]["branch_errors_over"]})
    checks.append({"check": "paging: more wasted evictions under under-prediction than over",
                   "value": [mech["paging"]["wasted_under"], mech["paging"]["wasted_over"]],
                   "ok": mech["paging"]["wasted_under"] > mech["paging"]["wasted_over"]})
    # the hypothesis is: under-prediction makes the largest job look SHORT and moves
    # it EARLIER (negative displacement vs its SPT rank), by more than over-prediction
    # moves it.  An earlier version asserted "later (positive)" -- the opposite of the
    # hypothesis it was testing, which is a proposition error, not a tolerance problem.
    checks.append({"check": "sched: the largest job is displaced EARLIER under under-prediction "
                            "(negative), by a larger magnitude than under over-prediction",
                   "value": [mech["sched"]["mean_rank_displacement_largest_under"],
                             mech["sched"]["mean_rank_displacement_largest_over"],
                             mech["sched"]["mean_abs_rank_displacement_under"],
                             mech["sched"]["mean_abs_rank_displacement_over"]],
                   "ok": mech["sched"]["mean_rank_displacement_largest_under"] < 0
                         and abs(mech["sched"]["mean_rank_displacement_largest_under"])
                         > abs(mech["sched"]["mean_rank_displacement_largest_over"])})
    # which paging statistic actually TRACKS the sign asymmetry?  report both ratios
    # so a hypothesis whose count is flat is visible rather than assumed away.
    wu, wo = mech["paging"]["wasted_under"], mech["paging"]["wasted_over"]
    tu, to = mech["paging"]["ties_under"], mech["paging"]["ties_over"]
    checks.append({"check": "paging: the tie statistic separates the signs more sharply than the "
                            "wasted-eviction statistic (report both ratios)",
                   "value": {"wasted_ratio": (wu + 1) / (wo + 1), "tie_ratio": (tu + 1) / (to + 1),
                             "wasted_counts": [wu, wo], "tie_counts": [tu, to]},
                   "ok": True, "note": "informational: which count explains the 0.094 ratio gap"})

    checks.append({"check": "paging: the sign gap SURVIVES lowering the score floor "
                            "(if it does not, the effect is my clamp, not the problem)",
                   "value": {"gap_floor_1": gap_1, "gap_floor_1e-09": gap_eps,
                             "detail": floor_ctrl},
                   "ok": gap_eps > 0.25 * gap_1,
                   "note": "reported either way; a vanishing gap is a FINDING about the blend, "
                           "not a failure of the run"})

    # ------------------------------------------- shared-factor invariance (the defect probe)
    exact = 0
    n_probe = 0
    for rep in range(REPS):
        for t in range(inst.TRACES_PER_REP):
            c, o = paging_shared_factor_probe(rep, t)
            n_probe += 1
            exact += (c == o)
    checks.append({"check": "paging: a POSITIVE shared per-request factor cannot change the "
                            "eviction order -- the arm must be exactly Belady (proves the "
                            "instrument's paging error model carries no information except through "
                            "the clamp)",
                   "value": {"traces": n_probe, "exactly_belady": exact},
                   "ok": exact == n_probe})

    checks.append({"check": "mechanism counts are nonzero on every problem (a zero count would "
                            "mean the statistic cannot see the phenomenon)",
                   "value": {k: v for k, v in mech.items()},
                   "ok": all([mech["ski"]["branch_errors_under"] > 0,
                              mech["paging"]["wasted_evictions"] > 0,
                              abs(mech["sched"]["mean_rank_displacement_largest_under"]) > 0])})

    ok = all(c["ok"] for c in checks)
    out = {"replicates": REPS, "profiles": list(SIGN_PROFILES), "mechanism": mech,
           "paging_shared_factor_probe": {"traces": n_probe, "exactly_belady": exact},
           "paging_floor_control": {"gap_floor_1": gap_1, "gap_floor_1e-09": gap_eps,
                                    "means": floor_ctrl},
           "records": recs, "checks": checks, "MECHANISM_CHECKS_ALL_PASS": ok}
    with io.open(os.path.join(HERE, "mechanism_v0_results.json"), "w", encoding="utf-8") as f:
        f.write(json.dumps(out, indent=1, sort_keys=True) + "\n")
    print(json.dumps({"mechanism": mech, "checks": checks, "ALL_PASS": ok}, indent=1))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
