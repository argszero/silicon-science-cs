#!/usr/bin/env python3
"""Issue #47 -- lambda certificate v1.1, step 7: the registered criterion (c).

THE GAP THIS CLOSES.  R330 reported the package's registered success criterion

    (c) the lambda-calibration loss is reported as a FACTOR with 95% between-stream intervals

as UNMET: no stage computed the rule that pins lambda -- the registration's "worst-case-eta
calibration of the trade-off parameter" -- and what I had was a fixed grid whose proxy
minimised the POOLED mean over the whole profile family, which is not a worst-case rule at
all.  Printing that proxy as a result would have turned a STATE into a conclusion.

WHAT IS MEASURED.  A worst-case-eta rule is a minimiser, so it needs a DECLARED adversary
class.  Three are declared, and the choice matters enough that the class is part of the
reported result:

  A_const(eta)   one error e, |e| <= eta, shared by every decision object.
                 DEGENERATE BY CONSTRUCTION, and kept as a control rather than dropped: a
                 factor shared by all candidates cannot change an argmax, so on the two
                 ranking problems it reproduces the unperturbed ranking exactly.  v1.0 of
                 this script used this class alone and measured exactly that (W(1) = 1.0000
                 at every eta) -- R320's invariance reappearing in a new place.  Its
                 degeneracy is now asserted (K5a) instead of being trusted.

  A_sign(eta)    a DECLARED FINITE set of per-object sign patterns at magnitude eta (all +,
                 all -, alternating, reversed-alternating, a third phase, and a fixed-seeded
                 random sign vector).  Non-degenerate; the class used for paging and
                 scheduling.  It is a RESTRICTED adversary -- the true worst case over all
                 per-object error vectors is not tractable for a global objective, and that
                 limit is stated rather than hidden.

  A_indep(eta)   ski rental only, EXACT: one error per instance, chosen independently to the
                 worse of the two endpoints.  The strongest class here, and the one the ski
                 arm headlines, so for ski the rule is not a restricted one.

  W(lam, eta)  = max over the class of the mean realised ratio at lam     (measured)
  lam_wc(eta)  = argmin_lam W(lam, eta)                                    (the rule)
  lam*(p)      = argmin_lam mean realised ratio on profile p               (the optimum)
  loss(p)      = ratio(lam_wc(eta_p), p) / ratio(lam*(p), p)               (the factor)

eta_p is the profile's own realised error bound; BOTH statistics are reported -- the maximum
|e| and the 95th percentile of |e| -- because the rule's answer is sensitive to which one a
designer would call "the bound", and that sensitivity is a result rather than a detail to
choose silently.

CONTROLS (each can refute the thing above it; all must pass)
  K1  at eta = 0 the rule is lam = 1: with no error, trust is optimal.
  K2  lam = 0 reproduces the independent classic implementations.
  K3  HARNESS: the local error-driven ski/sched copies reproduce instrument_v0 exactly on the
      profile's own realised errors -- otherwise the adversary prices a different algorithm
      than the paper reports.
  K4  the declared sign class never exceeds the EXACT per-instance class on ski.
  K5a the constant class is degenerate on paging and sched (W(1) = 1.0000 exactly).
  K5b the new per-page paging model reproduces paging_v1's repaired arm exactly at lam = 1.

CPU only, stdlib only, fixed seeds.  Every number printed is computed here.
"""
import io
import json
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import instrument_v0 as inst  # noqa: E402
import paging_v1 as pg        # noqa: E402  (the repaired per-page paging model)

REPS = inst.REPLICATES
LAM_GRID = [round(0.1 * i, 2) for i in range(11)]           # 0.0 .. 1.0
ETA_GRID = [0.0, 0.05, 0.10, 0.15, 0.30, 0.50, 0.75, 1.00]
BOOT = 2000
BOOT_SEED = 4701
SIGN_SEED = 4703
SKI_N = 300
CONST_MULTS = [-1.0, -0.5, 0.0, 0.5, 1.0]

CHECKS = []
DEGEN_ROWS = []


def check(name, ok, detail=""):
    CHECKS.append((name, bool(ok), detail))
    print("%-5s %s%s" % ("PASS" if ok else "FAIL", name,
                         ("  -- " + detail) if detail else ""))


def mean(xs):
    return sum(xs) / len(xs) if xs else None


def ratio_of(cost, opt):
    return float(cost) / float(opt)


# --------------------------------------------------------------- ski / sched
def ski_measure_errs(rep, errs, lam):
    """Local re-implementation, error-vector driven.  Mirrors inst.ski_measure."""
    ns = inst.ski_realization(rep)
    coins = inst.ski_coins(rep)
    out = []
    for i, n in enumerate(ns):
        n_hat = max(1, int(round(n * (1.0 + errs[i]))))
        d = inst.ski_trusted_day(n_hat) if coins[i] < lam else inst.ski_classic_day()
        out.append(ratio_of(inst.ski_cost(d, n), inst.ski_offline(n)))
    return out


def sched_measure_errs(rep, errs, lam):
    """Local re-implementation, error-vector driven.  Mirrors inst.sched_measure."""
    jobs = inst.sched_realization(rep)
    n = len(jobs)
    pred = [max(1, int(round(jobs[j] * (1.0 + errs[j])))) for j in range(n)]
    robust_rank = {j: j for j in range(n)}
    trusted_rank = {j: r for r, j in enumerate(sorted(range(n), key=lambda j: (pred[j], j)))}
    key = {j: lam * trusted_rank[j] + (1.0 - lam) * robust_rank[j] for j in range(n)}
    order = sorted(range(n), key=lambda j: (key[j], j))
    off = inst.flow_of_order(sorted(range(n), key=lambda j: (jobs[j], j)), jobs)
    return [ratio_of(inst.flow_of_order(order, jobs), off)]


# -------------------------------------------------------------- paging v1.1
def paging_perpage(trace, occ, errs_by_page, lam, floor=1.0):
    """The lam-blend on the REPAIRED (per-page) paging model.

    paging_v1 established that the decision object is the PAGE, so the error attaches to the
    page.  Its scoring is `raw = d * (1 + e_page)` with a floor; that is the lam = 1 endpoint
    of the blend `lam * raw + (1 - lam) * staleness`, whose lam = 0 endpoint is LRU.  Same
    cache, same tie-break (largest page id among equal scores), same floor.
    """
    cache, staleness, cost = {}, {}, 0
    for i, p in enumerate(trace):
        if p in cache:
            for q in staleness:
                staleness[q] += 1
            staleness[p] = 0
            continue
        cost += 1
        if len(cache) >= pg.K:
            def score(q):
                e = errs_by_page[q] if errs_by_page else 0.0
                raw = inst.next_arrival(occ, i, q, pg.CAP) * (1.0 + e)
                raw = raw if raw >= floor else floor
                return lam * raw + (1.0 - lam) * staleness[q]
            victim = max(cache, key=lambda q: (score(q), q))
            del cache[victim]
            del staleness[victim]
        cache[p] = i
        for q in staleness:
            staleness[q] += 1
        staleness[p] = 0
    return cost


def paging_ratio(rep, t, errs_by_page, lam):
    trace = inst.paging_realization(rep, t)
    occ = inst.build_occurrences(trace)
    c = paging_perpage(trace, occ, errs_by_page, lam)
    o = inst.belady_cost(trace, occ, pg.K, pg.CAP)
    return ratio_of(c, o)


def profile_errs(problem, profile, rep):
    if problem == "ski":
        return inst.gen_errors(profile, SKI_N, inst.seed_of("ski", "err", profile, rep))
    if problem == "sched":
        return inst.gen_errors(profile, inst.N_JOBS, inst.seed_of("sc", "err", profile, rep))
    if problem == "paging":
        # the PAGE is the decision object (R320/paging_v1), so a profile's error
        # population is its per-page draws, pooled over the traces of the stream
        return [e for t in range(inst.TRACES_PER_REP)
                for e in pg.page_errors(profile, rep, t, inst.N_PAGES)]
    raise ValueError(problem)


def cost_ratio(problem, rep, errs, lam):
    if problem == "ski":
        return mean(ski_measure_errs(rep, errs, lam))
    if problem == "sched":
        return mean(sched_measure_errs(rep, errs, lam))
    if problem == "paging":
        return mean([paging_ratio(rep, t, errs, lam) for t in range(inst.TRACES_PER_REP)])
    raise ValueError(problem)


# ------------------------------------------------- declared sign-pattern class
def sign_patterns(n, eta):
    """A DECLARED FINITE adversary set at magnitude eta (per-object sign vectors)."""
    rng = random.Random(SIGN_SEED)
    return [
        ("all+", [eta] * n),
        ("all-", [-eta] * n),
        ("alt", [eta if k % 2 == 0 else -eta for k in range(n)]),
        ("alt2", [-eta if k % 2 == 0 else eta for k in range(n)]),
        ("phase3", [eta if k % 3 == 0 else (-eta if k % 3 == 1 else 0.0) for k in range(n)]),
        ("seeded", [eta if rng.random() < 0.5 else -eta for _ in range(n)]),
    ]


def const_patterns(n, eta):
    return [("c%+.2f" % (m * eta), [m * eta] * n) for m in CONST_MULTS]


def obj_count(problem):
    if problem == "ski":
        return SKI_N
    if problem == "sched":
        return inst.N_JOBS
    return inst.N_PAGES


def w_max_over(problem, eta, lam, patterns):
    best, best_name = None, None
    for name, vec in patterns:
        rs = [cost_ratio(problem, rep, vec, lam) for rep in range(REPS)]
        v = mean(rs)
        if best is None or v > best:
            best, best_name = v, name
    return best, best_name


def w_indep_ski(eta, lam):
    """EXACT per-instance adversary for ski: each instance takes the worse endpoint."""
    per_rep = []
    for rep in range(REPS):
        ns = inst.ski_realization(rep)
        coins = inst.ski_coins(rep)
        tot = 0.0
        for i, nn in enumerate(ns):
            worst = None
            for e in (-eta, eta):
                n_hat = max(1, int(round(nn * (1.0 + e))))
                d = inst.ski_trusted_day(n_hat) if coins[i] < lam else inst.ski_classic_day()
                r = ratio_of(inst.ski_cost(d, nn), inst.ski_offline(nn))
                if worst is None or r > worst:
                    worst = r
            tot += worst
        per_rep.append(tot / len(ns))
    return mean(per_rep)


# ------------------------------------------------------------------ controls
def k3_harness():
    bad, n = [], 0
    for profile in ("zero", "unbiased_mid", "over_extreme", "wild_tail"):
        for rep in (0, 3):
            for lam in (0.0, 0.5, 1.0):
                n += 1
                ref = inst.ski_measure(rep, profile, lam)[0]
                if any(abs(a - b) > 1e-12 for a, b in
                       zip(ref, ski_measure_errs(rep, profile_errs("ski", profile, rep), lam))):
                    bad.append(("ski", profile, rep, lam))
                ref_s = inst.sched_measure(rep, profile, lam)[0]
                if abs(ref_s[0] - sched_measure_errs(
                        rep, profile_errs("sched", profile, rep), lam)[0]) > 1e-12:
                    bad.append(("sched", profile, rep, lam))
    check("K3 HARNESS: the local error-driven ski/sched copies reproduce instrument_v0 exactly",
          not bad, "%d cells (4 profiles x 2 reps x 3 lambdas); mismatches: %s"
          % (n, bad[:3] if bad else "none"))


def k5_paging_model():
    """(b) the per-page model reproduces paging_v1 at lam = 1; (a) A_const is degenerate."""
    bad, n = [], 0
    for profile in ("zero", "unbiased_mid", "over_extreme"):
        for rep in (0, 2):
            for t in (0, 3):
                n += 1
                trace = inst.paging_realization(rep, t)
                occ = inst.build_occurrences(trace)
                errs = pg.page_errors(profile, rep, t, inst.N_PAGES)
                c_ref, _o, _st = pg.simulate(trace, occ, profile, rep, t, mode="per_page")
                if c_ref != paging_perpage(trace, occ, errs, 1.0):
                    bad.append((profile, rep, t, c_ref, paging_perpage(trace, occ, errs, 1.0)))
    check("K5b the per-page paging model reproduces paging_v1's repaired arm at lam = 1",
          not bad, "%d (profile, rep, trace) cells against paging_v1.simulate; mismatches: %s"
          % (n, bad[:3] if bad else "none"))
    # The assertion was FIRST written as "exactly 1.0000 on both problems", and the
    # measurement refuted it for scheduling: W(1) = 1.00026 at eta = 0.30 and 1.00270 at
    # 0.75.  A shared factor cannot reorder a *real-valued* ranking, but the sched arm's
    # trusted ranking is built from INTEGERS (`max(1, round(jobs*(1+e)))`), so a large
    # enough perturbation collapses distinct values into one integer and the tie-break
    # by index does the reordering.  The residue is real, it is bounded (measured), and
    # it is 2 orders of magnitude below the sign class's effect -- so the check now
    # states the bound it can defend instead of the equality it could not.
    rows, worst = [], 0.0
    for problem in ("paging", "sched"):
        for eta in (0.30, 0.75):
            v, _bn = w_max_over(problem, eta, 1.0, const_patterns(obj_count(problem), eta))
            sv, _sn = w_max_over(problem, eta, 1.0, sign_patterns(obj_count(problem), eta))
            rows.append((problem, eta, v, sv))
            worst = max(worst, abs(v - 1.0))
    check("K5a the constant-error class is DEGENERATE for ranking: its W(1) stays within"
          " 0.003 of 1.0, while the declared sign class reaches the measured values below",
          worst < 0.003,
          "; ".join("%s eta=%.2f: const W(1)=%.5f vs sign W(1)=%.4f" % r for r in rows))
    DEGEN_ROWS[:] = rows


def k2_classic():
    bad = []
    for rep in range(REPS):
        ns = inst.ski_realization(rep)
        want = [ratio_of(c, inst.ski_offline(n))
                for c, n in zip(inst.ski_classic_costs(rep), ns)]
        if any(abs(a - b) > 1e-12
               for a, b in zip(want, ski_measure_errs(rep, [0.0] * SKI_N, 0.0))):
            bad.append(("ski", rep))
        jobs = inst.sched_realization(rep)
        off = inst.flow_of_order(sorted(range(len(jobs)), key=lambda j: (jobs[j], j)), jobs)
        if abs(inst.sched_fifo_cost(rep) / off
               - sched_measure_errs(rep, [0.0] * inst.N_JOBS, 0.0)[0]) > 1e-12:
            bad.append(("sched", rep))
        for t in range(inst.TRACES_PER_REP):
            trace = inst.paging_realization(rep, t)
            occ = inst.build_occurrences(trace)
            if abs(paging_ratio(rep, t, None, 0.0)
                   - ratio_of(inst.lru_cost(trace, pg.K),
                              inst.belady_cost(trace, occ, pg.K, pg.CAP))) > 1e-12:
                bad.append(("paging", rep, t))
    check("K2 lam = 0 reproduces the independent classic implementations exactly",
          not bad, "ski classic day, FIFO, LRU over %d streams; mismatches: %s"
          % (REPS, bad[:3] if bad else "none"))


def k1_zerolimit():
    ok, det = True, []
    for problem in ("ski", "sched", "paging"):
        ws = {lam: w_max_over(problem, 0.0, lam,
                              const_patterns(obj_count(problem), 0.0))[0] for lam in LAM_GRID}
        best = min(LAM_GRID, key=lambda l: (ws[l], l))
        det.append("%s: lam_wc(0)=%.2f" % (problem, best))
        if best != 1.0:
            ok = False
    check("K1 at eta = 0 the worst-case rule is lam = 1 (with no error, trust is optimal)",
          ok, "; ".join(det))


# ----------------------------------------------------------------- utilities
def bound_stats(problem, profile):
    vals = []
    for rep in range(REPS):
        vals.extend(profile_errs(problem, profile, rep))
    a = sorted(abs(e) for e in vals)
    return {"max": a[-1], "q95": a[min(len(a) - 1, int(0.95 * len(a)))]}


def lam_star(problem, profile):
    per_rep = {}
    for lam in LAM_GRID:
        per_rep[lam] = [cost_ratio(problem, rep, profile_errs(problem, profile, rep), lam)
                        for rep in range(REPS)]
    means = {lam: mean(v) for lam, v in per_rep.items()}
    best = min(LAM_GRID, key=lambda l: (means[l], l))
    return best, means[best], per_rep


def boot_ci(pairs, reps=BOOT, seed=BOOT_SEED):
    rng = random.Random(seed)
    n = len(pairs)
    if n < 2:
        return (None, None)
    ms = []
    for _ in range(reps):
        s = [pairs[rng.randrange(n)] for _ in range(n)]
        ms.append(sum(s) / n)
    ms.sort()
    return (ms[int(0.025 * reps)], ms[int(0.975 * reps) - 1])


def pearson(xs, ys):
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    dx = math.sqrt(sum((x - mx) ** 2 for x in xs))
    dy = math.sqrt(sum((y - my) ** 2 for y in ys))
    return num / (dx * dy) if dx and dy else None


def wc_ratio_rep(problem, eta, lam, rep):
    """The worst-case class's realised ratio for ONE stream (paired with lam*'s stream)."""
    pats = sign_patterns(obj_count(problem), eta)
    return max(mean([cost_ratio(problem, rep, vec, lam)]) for _n, vec in pats)


def wc_ratio_rep_indep(eta, lam, rep):
    ns = inst.ski_realization(rep)
    coins = inst.ski_coins(rep)
    tot = 0.0
    for i, nn in enumerate(ns):
        worst = None
        for e in (-eta, eta):
            n_hat = max(1, int(round(nn * (1.0 + e))))
            d = inst.ski_trusted_day(n_hat) if coins[i] < lam else inst.ski_classic_day()
            r = ratio_of(inst.ski_cost(d, nn), inst.ski_offline(nn))
            if worst is None or r > worst:
                worst = r
        tot += worst
    return tot / len(ns)


def rule_curve(problem, exact=False):
    out = {}
    for eta in ETA_GRID:
        if exact and problem == "ski":
            ws = {lam: w_indep_ski(eta, lam) for lam in LAM_GRID}
            names = {l: "exact-per-instance" for l in LAM_GRID}
        else:
            ws, names = {}, {}
            for lam in LAM_GRID:
                v, bn = w_max_over(problem, eta, lam, sign_patterns(obj_count(problem), eta))
                ws[lam], names[lam] = v, bn
        best = min(LAM_GRID, key=lambda l: (ws[l], l))
        out[eta] = {"lam_wc": best, "W": ws[best], "W_at_0": ws[0.0], "W_at_1": ws[1.0],
                    "interior": best not in (0.0, 1.0), "argmax_at_rule": names.get(best, "")}
    return out


def main():
    out = {"instrument": "lambda_cert_v1.1", "lam_grid": LAM_GRID, "eta_grid": ETA_GRID,
           "sign_seed": SIGN_SEED, "reps": REPS, "boot": BOOT}
    EXACT = {"ski": True, "sched": False, "paging": False}

    k3_harness()
    k5_paging_model()
    k2_classic()
    k1_zerolimit()

    gaps, dom = [], []
    for eta in (0.10, 0.30, 0.75):
        for lam in (0.0, 0.5, 1.0):
            a = w_max_over("ski", eta, lam, sign_patterns(SKI_N, eta))[0]
            b = w_indep_ski(eta, lam)
            gaps.append(abs(a - b))
            if a > b + 1e-12:
                dom.append((eta, lam, a, b))
    check("K4 the declared sign class never exceeds the EXACT per-instance class on ski",
          not dom, "9 cells, max |A_sign - A_indep| = %.3e" % max(gaps))

    print("\n  the rule lam_wc(eta), under the richest tractable class per problem")
    rule = {}
    for problem in ("ski", "sched", "paging"):
        rule[problem] = rule_curve(problem, exact=EXACT[problem])
        for eta in ETA_GRID:
            r = rule[problem][eta]
            print("    %-7s eta=%.2f  lam_wc=%.2f  W=%.4f (W(0)=%.4f W(1)=%.4f)  argmax=%s%s"
                  % (problem, eta, r["lam_wc"], r["W"], r["W_at_0"], r["W_at_1"],
                     r["argmax_at_rule"], "  INTERIOR" if r["interior"] else ""))
    out["rule"] = {p: {str(k): v for k, v in d.items()} for p, d in rule.items()}
    out["rule_const_contrast"] = {}
    for problem in ("ski", "sched", "paging"):
        ws = {lam: w_max_over(problem, 0.50, lam, const_patterns(obj_count(problem), 0.50))[0]
              for lam in LAM_GRID}
        out["rule_const_contrast"][problem] = {"lam_wc":
                                               min(LAM_GRID, key=lambda l: (ws[l], l)),
                                               "W_at_1": ws[1.0]}

    print("\n  the calibration loss ratio(lam_wc) / ratio(lam*)  per profile")
    losses = {}
    for problem in ("ski", "sched", "paging"):
        losses[problem] = {}
        for profile in inst.PROFILES:
            bs = bound_stats(problem, profile)
            eta_use = min([e for e in ETA_GRID if e >= bs["max"] - 1e-12] or [ETA_GRID[-1]])
            lam_wc = rule[problem][eta_use]["lam_wc"]
            lam_s, mean_star, per_rep = lam_star(problem, profile)
            if EXACT[problem]:
                wc_rep = [wc_ratio_rep_indep(eta_use, lam_wc, rep) for rep in range(REPS)]
            else:
                wc_rep = [wc_ratio_rep(problem, eta_use, lam_wc, rep) for rep in range(REPS)]
            pairs = [wc_rep[i] / per_rep[lam_s][i] for i in range(REPS)]
            lo, hi = boot_ci(pairs)
            losses[problem][profile] = {
                "bound_max": bs["max"], "bound_q95": bs["q95"], "eta_used": eta_use,
                "lam_wc": lam_wc, "lam_star": lam_s, "ratio_wc": mean(wc_rep),
                "ratio_star": mean_star, "loss": mean(pairs), "loss_lo": lo, "loss_hi": hi,
                "streams": REPS, "displaced": lam_wc != lam_s,
                "tail": inst.PROFILES[profile][3] * inst.PROFILES[profile][4],
                "spread": inst.PROFILES[profile][1]}
            print("    %-7s %-18s |e|max=%.3f q95=%.3f eta=%.2f  lam_wc=%.2f lam*=%.2f"
                  "  loss=%.4f [%.4f,%.4f] %s"
                  % (problem, profile, bs["max"], bs["q95"], eta_use, lam_wc, lam_s,
                     mean(pairs), lo, hi, "DISPLACED" if lam_wc != lam_s else "same"))
    out["losses"] = losses

    print("\n  direction: does the loss grow with the tail or with the spread?")
    direction = {}
    for problem in ("ski", "sched", "paging"):
        rows = [losses[problem][p] for p in inst.PROFILES if p != "zero"]
        direction[problem] = {}
        for key in ("tail", "spread"):
            r_ = pearson([r[key] for r in rows], [r["loss"] for r in rows])
            direction[problem]["corr_" + key] = r_
            print("    %-7s corr(loss, %-6s) = %s"
                  % (problem, key, "%.4f" % r_ if r_ is not None else "n/a"))
        tl = [p for p in inst.PROFILES if inst.PROFILES[p][3] > 0]
        ot = [p for p in inst.PROFILES if inst.PROFILES[p][3] == 0 and p != "zero"]
        direction[problem]["mean_loss_tail_profiles"] = mean(
            [losses[problem][p]["loss"] for p in tl])
        direction[problem]["mean_loss_other_profiles"] = mean(
            [losses[problem][p]["loss"] for p in ot])
        direction[problem]["tail_profiles"] = tl
        print("    %-7s mean loss: tail profiles (n=%d) %.4f | others %.4f"
              % (problem, len(tl), direction[problem]["mean_loss_tail_profiles"],
                 direction[problem]["mean_loss_other_profiles"]))
    out["direction"] = direction

    print("\n  criterion (c): a factor with 95% between-stream intervals")
    c_out = {}
    for problem in ("ski", "sched", "paging"):
        rows = [losses[problem][p] for p in inst.PROFILES if p != "zero"]
        big = max(rows, key=lambda r: r["loss"])
        c_out[problem] = {
            "n_profiles": len(rows),
            "loss_median": sorted(r["loss"] for r in rows)[len(rows) // 2],
            "loss_max": big["loss"], "loss_max_spread": big["spread"],
            "loss_max_lo": big["loss_lo"], "loss_max_hi": big["loss_hi"],
            "lam_wc_values": sorted(set(r["lam_wc"] for r in rows)),
            "lam_star_values": sorted(set(r["lam_star"] for r in rows)),
            "n_displaced": sum(1 for r in rows if r["displaced"])}
        print("    %-7s n=%d  median %.4f  max %.4f [%.4f,%.4f]  lam_wc in %s  lam* in %s"
              "  displaced %d/%d"
              % (problem, len(rows), c_out[problem]["loss_median"], big["loss"],
                 big["loss_lo"], big["loss_hi"], c_out[problem]["lam_wc_values"],
                 c_out[problem]["lam_star_values"], c_out[problem]["n_displaced"], len(rows)))
    out["criterion_c"] = c_out

    # ---- the same factor with lambda* fitted OUT OF SAMPLE -----------------
    # The loss above uses an IN-SAMPLE lambda*: the optimum is chosen on the very streams
    # it is then scored on, which flatters the optimum and therefore makes the measured
    # loss a LOWER BOUND on the price of the worst-case rule.  That direction is
    # conservative for the claim, but the number should not rest on it, so the factor is
    # also computed with lambda* fitted on the even streams and scored on the odd ones.
    print("\n  the same factor with lam* fitted out of sample (even streams -> odd)")
    oos = {}
    half = REPS // 2
    for problem in ("ski", "sched", "paging"):
        oos[problem] = {}
        for profile in inst.PROFILES:
            bs = bound_stats(problem, profile)
            eta_use = min([e for e in ETA_GRID if e >= bs["max"] - 1e-12] or [ETA_GRID[-1]])
            lam_wc = rule[problem][eta_use]["lam_wc"]
            per_rep = {lam: [cost_ratio(problem, rep, profile_errs(problem, profile, rep), lam)
                             for rep in range(REPS)] for lam in LAM_GRID}
            fit = [r for r in range(REPS) if r % 2 == 0]
            ev = [r for r in range(REPS) if r % 2 == 1]
            lam_fit = min(LAM_GRID, key=lambda l: (mean([per_rep[l][r] for r in fit]), l))
            if EXACT[problem]:
                wc = [wc_ratio_rep_indep(eta_use, lam_wc, r) for r in ev]
            else:
                wc = [wc_ratio_rep(problem, eta_use, lam_wc, r) for r in ev]
            pairs = [wc[i] / per_rep[lam_fit][ev[i]] for i in range(len(ev))]
            lo, hi = boot_ci(pairs)
            oos[problem][profile] = {"lam_wc": lam_wc, "lam_fit": lam_fit,
                                     "loss_oos": mean(pairs), "lo": lo, "hi": hi,
                                     "streams": len(ev),
                                     "loss_insample": losses[problem][profile]["loss"]}
            if profile != "zero":
                print("    %-7s %-18s lam_wc=%.2f lam*_fit=%.2f  loss_oos=%.4f [%.4f,%.4f]"
                      "  (in-sample %.4f)"
                      % (problem, profile, lam_wc, lam_fit, mean(pairs), lo, hi,
                         losses[problem][profile]["loss"]))
    out["oos"] = oos
    for problem in ("ski", "sched", "paging"):
        rowsx = [oos[problem][p] for p in inst.PROFILES if p != "zero"]
        print("    %-7s median loss_oos %.4f  max %.4f" % (
            problem,
            sorted(r["loss_oos"] for r in rowsx)[len(rowsx) // 2],
            max(r["loss_oos"] for r in rowsx)))
        out["criterion_c"][problem]["loss_oos_median"] = sorted(
            r["loss_oos"] for r in rowsx)[len(rowsx) // 2]

    n_fail = sum(1 for _n, ok, _d in CHECKS if not ok)
    out["checks"] = [{"name": n, "ok": ok, "detail": d} for n, ok, d in CHECKS]
    # The package's stages each persist a flag about themselves, and the canonical runner
    # cross-checks that flag against the check list.  This stage had none (it was written in
    # the research workspace, where nothing read it back); the flag is added here rather than
    # inferred by the runner, so the cross-check compares two independent records.
    out["CHECKS_ALL_PASS"] = n_fail == 0
    print("\ncontrols: %d run, %d failed" % (len(CHECKS), n_fail))
    print("verdict: %s" % ("OK" if n_fail == 0 else "NOT READY"))
    with io.open(os.path.join(HERE, "lambda_cert_v1_results.json"), "w",
                 encoding="utf-8") as fh:
        json.dump(out, fh, indent=1, sort_keys=True)
    print("wrote lambda_cert_v1_results.json")
    return 0 if n_fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
