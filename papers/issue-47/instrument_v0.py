#!/usr/bin/env python3
"""Issue #47 -- instrument v0.1, step 3 (supersedes v0).

v0 had two real defects, both found by the END ANCHORS and both recorded:

  D1 (realization confound).  The instance draw was seeded with the PROFILE
     name, so at lambda=0 -- where the blend provably ignores the prediction --
     the per-stream means still differed between profiles (zero: 1.7722, 1.7491,
     ...; over_mid: 1.7491, 1.6963, ...).  A profile "effect" measured that way
     is the run draw, credited to the component under test.
     Fix: ONE realization per (problem, replicate), shared by every profile and
     every lambda, so all cells are paired by construction.  The lambda=0 check
     is then exact: identical ratios across all 8 profiles.

  D2 (proposition error).  The classic ski-rental bound 2 - r/b is a WORST CASE;
     I checked a MEAN (1.766 vs 1.99).  The correct statement is exactly
     satisfied (max ratio = 1.99 at r=1, b=100).  Restated, not loosened.

Both designs are now testable rather than asserted: lambda=0 must reproduce the
classic algorithm computed by an INDEPENDENT implementation (LRU, FIFO, the
classic buy day), and lambda=1 with zero error must return the exact offline
optimum.  No claim is made here; the measurement columns are for the next step.
"""
import bisect, io, json, math, os, random, sys, zlib

HERE = os.path.dirname(os.path.abspath(__file__))

PROFILES = {
    # name: (bias mu, spread sigma, AR(1) rho, tail_prob, tail_mult)
    # -- the small-error block: lambda=1 is already near-optimal here
    "zero":             (0.00, 0.00, 0.0, 0.00, 1.0),
    "unbiased_low":     (0.00, 0.05, 0.0, 0.00, 1.0),
    "unbiased_mid":     (0.00, 0.15, 0.0, 0.00, 1.0),
    "unbiased_high":    (0.00, 0.30, 0.0, 0.00, 1.0),
    "over_mid":         (+0.15, 0.15, 0.0, 0.00, 1.0),
    "under_mid":        (-0.15, 0.15, 0.0, 0.00, 1.0),
    "ar_mid":           (0.00, 0.15, 0.6, 0.00, 1.0),
    "tail_mid":         (0.00, 0.15, 0.0, 0.05, 5.0),
    # -- the large-error block: this is where the robust arm can compete, so it is
    #    the regime in which a lambda trade-off exists at all.  Without it the
    #    "worst-case lambda costs a factor" question is a null by construction.
    "unbiased_veryhigh":(0.00, 0.60, 0.0, 0.00, 1.0),
    "unbiased_extreme": (0.00, 1.00, 0.0, 0.00, 1.0),
    "over_extreme":     (+0.50, 0.50, 0.0, 0.00, 1.0),
    "under_extreme":    (-0.50, 0.50, 0.0, 0.00, 1.0),
    "wild_tail":        (0.00, 0.30, 0.0, 0.10, 8.0),
}
LAMBDAS = [0.0, 0.25, 0.5, 0.75, 1.0]
REPLICATES = 16         # raised: MDE must sit BELOW the effects of interest
TRACES_PER_REP = 4
K_PAGES = 5
TRACE_LEN = 1200
N_PAGES = 10
N_JOBS = 300            # raised: the sched cell was the resolution bottleneck
SKI_R, SKI_B = 1, 100
SKI_N_RANGE = (5, 400)


def seed_of(*parts):
    return zlib.crc32("|".join(str(p) for p in parts).encode("utf-8"))


def gen_errors(name, n, seed):
    mu, sig, rho, ptail, tmult = PROFILES[name]
    rng = random.Random(seed)
    out, z = [], 0.0
    for _ in range(n):
        z = rho * z + math.sqrt(max(0.0, 1.0 - rho * rho)) * rng.gauss(0.0, 1.0)
        s = sig * (tmult if (ptail > 0 and rng.random() < ptail) else 1.0)
        out.append(mu + s * z)
    return out


def profile_stats(errs):
    pos = [e for e in errs if e > 0]
    neg = [e for e in errs if e < 0]
    a = sorted(abs(e) for e in errs)
    n = len(a)
    q95 = a[min(n - 1, int(0.95 * n))] if n else 0.0
    mean_abs = sum(a) / n if n else 0.0
    pos_mean = sum(pos) / len(pos) if pos else 0.0
    neg_mean = sum(neg) / len(neg) if neg else 0.0
    mean = sum(errs) / n if n else 0.0
    sd = math.sqrt(sum((e - mean) ** 2 for e in errs) / n) if n else 0.0
    return {"mean_abs": mean_abs, "pos_mean": pos_mean, "neg_mean": neg_mean,
            "sd": sd, "q95_abs": q95, "flip_rate": (len(pos) + len(neg)) / n if n else 0.0}


# =============================================================== ski rental
def ski_offline(n):
    return min(n * SKI_R, SKI_B)


def ski_cost(d_buy, n):
    if d_buy is None or d_buy > n:
        return n * SKI_R
    return (d_buy - 1) * SKI_R + SKI_B


def ski_classic_day():
    return max(1, int(math.ceil(SKI_B / SKI_R)))


def ski_trusted_day(n_hat):
    return 1 if n_hat * SKI_R >= SKI_B else None


def ski_realization(rep):
    rng = random.Random(seed_of("ski", "real", rep))
    return [rng.randrange(SKI_N_RANGE[0], SKI_N_RANGE[1]) for _ in range(300)]


def ski_coins(rep):
    """Common random numbers: ONE uniform per instance, shared by every lambda and
    every profile.  Taking the trusted action iff u_i < lambda makes the sweep a
    NESTED mixture, so the lambda columns are paired rather than independently
    redrawn (v0 redrew the coin per lambda, which is why its sweep was not the
    mixture it looked like)."""
    rng = random.Random(seed_of("ski", "coin", rep))
    return [rng.random() for _ in range(300)]


def ski_measure(rep, profile, lam):
    ns = ski_realization(rep)
    errs = gen_errors(profile, len(ns), seed_of("ski", "err", profile, rep))
    coins = ski_coins(rep)
    ratios, costs = [], []
    for i, n in enumerate(ns):
        n_hat = max(1, int(round(n * (1.0 + errs[i]))))
        d = ski_trusted_day(n_hat) if coins[i] < lam else ski_classic_day()
        c = ski_cost(d, n)
        costs.append(c)
        ratios.append(c / ski_offline(n))
    return ratios, costs, errs


def ski_classic_costs(rep):
    """INDEPENDENT implementation of the lambda=0 algorithm."""
    return [ski_cost(ski_classic_day(), n) for n in ski_realization(rep)]


# =================================================================== paging
def build_occurrences(trace):
    occ = {}
    for i, p in enumerate(trace):
        occ.setdefault(p, []).append(i)
    return occ


def next_arrival(occ, i, page, cap):
    lst = occ.get(page)
    if not lst:
        return cap
    j = bisect.bisect_right(lst, i)
    return cap if j >= len(lst) else lst[j] - i


def paging_cost(trace, occ, k, lam, errs, cap):
    cache, staleness, cost = {}, {}, 0
    for i, p in enumerate(trace):
        if p in cache:
            for q in staleness:
                staleness[q] += 1
            staleness[p] = 0
            continue
        cost += 1
        if len(cache) >= k:
            e = errs[i] if errs is not None else 0.0
            def score(q):
                d = next_arrival(occ, i, q, cap)
                if errs is not None:
                    d = max(1.0, d * (1.0 + e))
                return lam * d + (1.0 - lam) * staleness[q]
            victim = max(cache, key=lambda q: (score(q), q))
            del cache[victim]
            del staleness[victim]
        cache[p] = i
        for q in staleness:
            staleness[q] += 1
        staleness[p] = 0
    return cost


def belady_cost(trace, occ, k, cap):
    cache, cost = set(), 0
    for i, p in enumerate(trace):
        if p in cache:
            continue
        cost += 1
        if len(cache) < k:
            cache.add(p)
        else:
            victim = max(cache, key=lambda q: (next_arrival(occ, i, q, cap), q))
            cache.discard(victim)
            cache.add(p)
    return cost


def lru_cost(trace, k):
    """INDEPENDENT implementation of LRU (a list, not the blend's score code)."""
    order, cost = [], 0
    for p in trace:
        if p in order:
            order.remove(p)
            order.append(p)
            continue
        cost += 1
        if len(order) >= k:
            order.pop(0)
        order.append(p)
    return cost


def paging_realization(rep, t):
    rng = random.Random(seed_of("pg", "real", rep, t))
    return [rng.randrange(N_PAGES) for _ in range(TRACE_LEN)]


def paging_measure(rep, profile, lam):
    ratios, costs = [], []
    for t in range(TRACES_PER_REP):
        trace = paging_realization(rep, t)
        occ = build_occurrences(trace)
        cap = TRACE_LEN + 1
        off = belady_cost(trace, occ, K_PAGES, cap)
        errs = None if lam == 0.0 else gen_errors(profile, TRACE_LEN, seed_of("pg", "err", profile, rep, t))
        c = paging_cost(trace, occ, K_PAGES, lam, errs, cap)
        costs.append(c)
        ratios.append(c / off)
    return ratios, costs, []


def paging_zero_profile_errors(rep):
    return [gen_errors("zero", TRACE_LEN, seed_of("pg", "err", "zero", rep, t))
            for t in range(TRACES_PER_REP)]


# =============================================================== scheduling
def flow_of_order(order, jobs):
    n = len(order)
    return sum((n - i) * jobs[order[i]] for i in range(n))


def sched_realization(rep):
    rng = random.Random(seed_of("sc", "real", rep))
    return [rng.randrange(1, 60) for _ in range(N_JOBS)]


def sched_measure(rep, profile, lam):
    jobs = sched_realization(rep)
    errs = gen_errors(profile, N_JOBS, seed_of("sc", "err", profile, rep))
    pred = [max(1, int(round(jobs[j] * (1.0 + errs[j])))) for j in range(N_JOBS)]
    robust_rank = {j: j for j in range(N_JOBS)}
    trusted_rank = {j: r for r, j in enumerate(sorted(range(N_JOBS), key=lambda j: (pred[j], j)))}
    key = {j: lam * trusted_rank[j] + (1.0 - lam) * robust_rank[j] for j in range(N_JOBS)}
    order = sorted(range(N_JOBS), key=lambda j: (key[j], j))
    off = flow_of_order(sorted(range(N_JOBS), key=lambda j: (jobs[j], j)), jobs)
    c = flow_of_order(order, jobs)
    return [c / off], [c], errs


def sched_fifo_cost(rep):
    jobs = sched_realization(rep)
    return flow_of_order(list(range(N_JOBS)), jobs)


# ==================================================================== driver
def main():
    rows = []
    for problem in ("ski", "paging", "sched"):
        for rep in range(REPLICATES):
            for profile in PROFILES:
                for lam in LAMBDAS:
                    if problem == "ski":
                        ratios, costs, errs = ski_measure(rep, profile, lam)
                    elif problem == "paging":
                        ratios, costs, errs = paging_measure(rep, profile, lam)
                    else:
                        ratios, costs, errs = sched_measure(rep, profile, lam)
                    st = profile_stats(errs) if errs else profile_stats(
                        gen_errors(profile, TRACE_LEN, seed_of("pg", "err", profile, rep, 0)))
                    rows.append({
                        "problem": problem, "replicate": rep, "profile": profile, "lam": lam,
                        "mean_ratio": sum(ratios) / len(ratios), "max_ratio": max(ratios),
                        "min_ratio": min(ratios), "n": len(ratios),
                        "mean_cost": sum(costs) / len(costs), "error": st,
                    })

    def cells(problem, profile, lam):
        return [r for r in rows if r["problem"] == problem and r["profile"] == profile and r["lam"] == lam]

    checks = []

    # A1 -- lambda=1 with a ZERO-error prediction returns the exact offline optimum
    for problem in ("ski", "paging", "sched"):
        cs = cells(problem, "zero", 1.0)
        v = sum(c["mean_ratio"] for c in cs) / len(cs)
        checks.append({"check": "A1 lam=1 & zero error == exact offline optimum (%s)" % problem,
                       "value": v, "ok": abs(v - 1.0) < 1e-12})

    # A2 -- lambda=0 ignores the prediction IDENTICALLY across all 8 profiles (paired by replicate)
    for problem in ("ski", "paging", "sched"):
        ref = [c["mean_ratio"] for c in sorted(cells(problem, "zero", 0.0), key=lambda c: c["replicate"])]
        worst = 0.0
        for profile in PROFILES:
            got = [c["mean_ratio"] for c in sorted(cells(problem, profile, 0.0), key=lambda c: c["replicate"])]
            worst = max(worst, max(abs(a - b) for a, b in zip(ref, got)))
        checks.append({"check": "A2 lam=0 is identical across all %d profiles (%s)"
                                % (len(PROFILES), problem),
                       "value": worst, "ok": worst < 1e-12})

    # A3 -- lambda=0 reproduces the classic algorithm by an INDEPENDENT implementation
    bad = 0
    for rep in range(REPLICATES):
        got = [c["mean_cost"] for c in cells("ski", "zero", 0.0) if c["replicate"] == rep][0]
        ref = sum(ski_classic_costs(rep)) / len(ski_classic_costs(rep))
        bad += (abs(got - ref) > 1e-12)
    checks.append({"check": "A3 lam=0 ski == independent classic buy-day implementation",
                   "value": bad, "ok": bad == 0})

    bad = 0
    for rep in range(REPLICATES):
        for t in range(TRACES_PER_REP):
            trace = paging_realization(rep, t)
            occ = build_occurrences(trace)
            got = paging_cost(trace, occ, K_PAGES, 0.0, None, TRACE_LEN + 1)
            bad += (got != lru_cost(trace, K_PAGES))
    checks.append({"check": "A4 lam=0 paging == independent LRU implementation (all traces)",
                   "value": bad, "ok": bad == 0})

    bad = 0
    for rep in range(REPLICATES):
        got = [c["mean_cost"] for c in cells("sched", "zero", 0.0) if c["replicate"] == rep][0]
        bad += (abs(got - sched_fifo_cost(rep)) > 1e-12)
    checks.append({"check": "A5 lam=0 scheduling == independent FIFO implementation",
                   "value": bad, "ok": bad == 0})

    # A6 -- the classic ski-rental WORST CASE (a worst case, not a mean)
    mx = max(c["max_ratio"] for c in rows if c["problem"] == "ski" and c["lam"] == 0.0)
    lb = 2 - SKI_R / SKI_B
    checks.append({"check": "A6 lam=0 ski worst-case ratio == 2 - r/b", "value": mx,
                   "ok": abs(mx - lb) < 1e-12})

    # A7 -- lambda=0 paging lies in (1, k]
    vals = [c["mean_ratio"] for c in rows if c["problem"] == "paging" and c["lam"] == 0.0]
    checks.append({"check": "A7 lam=0 paging ratio inside (1, k]", "value": max(vals),
                   "ok": 1.0 < min(vals) and max(vals) <= K_PAGES + 1e-12})

    # A8 -- no algorithm beats the exact offline optimum anywhere (a lower bound)
    viol = sum(1 for r in rows if r["min_ratio"] < 1.0 - 1e-12)
    checks.append({"check": "A8 no cell goes below the exact offline optimum", "value": viol,
                   "ok": viol == 0})

    # A9 -- SCOPE: the RANDOMIZED ski blend only.  With common random numbers its
    # sweep is a nested mixture of two fixed actions, so every intermediate lambda
    # must lie inside the endpoint bracket.  The paging and scheduling blends
    # interpolate SCORES / ORDERS, not actions -- an intermediate order is neither
    # endpoint, and can beat both (measured: sched, rep=15, unbiased_extreme,
    # lambda=0.75 -> 1.2775 against the bracket [1.2854, 1.4451]).  Asserting the
    # mixture property there was a proposition error, not a defect in the blend.
    # Monotonicity is not asserted anywhere: an instance may prefer the robust action.
    viol = 0
    for rep in range(REPLICATES):
        for profile in PROFILES:
            e0 = [c["mean_ratio"] for c in cells("ski", profile, 0.0) if c["replicate"] == rep][0]
            e1 = [c["mean_ratio"] for c in cells("ski", profile, 1.0) if c["replicate"] == rep][0]
            lo, hi = min(e0, e1), max(e0, e1)
            for lam in (0.25, 0.5, 0.75):
                v = [c["mean_ratio"] for c in cells("ski", profile, lam) if c["replicate"] == rep][0]
                if v < lo - 1e-12 or v > hi + 1e-12:
                    viol += 1
    checks.append({"check": "A9 [randomized blend only] intermediate lambda inside the bracket",
                   "value": viol, "ok": viol == 0})

    # A10 -- lambda=1 with zero error is exact PER INSTANCE, not merely on average
    mx = max((c["max_ratio"] for c in cells("ski", "zero", 1.0)), default=0.0)
    mx = max(mx, max((c["max_ratio"] for c in cells("sched", "zero", 1.0)), default=0.0))
    mx = max(mx, max((c["max_ratio"] for c in cells("paging", "zero", 1.0)), default=0.0))
    checks.append({"check": "A10 lam=1 & zero error: worst instance is the optimum too",
                   "value": mx, "ok": abs(mx - 1.0) < 1e-12})

    ok = all(c["ok"] for c in checks)
    out = {"profiles": PROFILES, "lambdas": LAMBDAS, "replicates": REPLICATES,
           "traces_per_rep": TRACES_PER_REP, "k_pages": K_PAGES, "trace_len": TRACE_LEN,
           "n_pages": N_PAGES, "n_jobs": N_JOBS, "ski": [SKI_R, SKI_B], "rows": rows,
           "checks": checks, "END_ANCHORS_ALL_PASS": ok}
    with io.open(os.path.join(HERE, "instrument_v0_results.json"), "w", encoding="utf-8") as f:
        f.write(json.dumps(out, indent=1, sort_keys=True) + "\n")
    print(json.dumps({"checks": checks, "END_ANCHORS_ALL_PASS": ok}, indent=1))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
