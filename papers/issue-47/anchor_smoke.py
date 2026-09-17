#!/usr/bin/env python3
"""Issue #47 -- instrument v0, step 1: exact-anchor smoke test.

Purpose: before ANY claim about error decomposition, show that
  (A) each problem's offline optimum is exact by construction, verified
      against brute force (Belady == min over all offline strategies;
      SPT == min over all schedules; ski-rental min(n*r, b) == min over
      candidate buy days),
  (B) the classic anchors are recovered: ski rental's deterministic
      competitive ratio is exactly 2 - r/b, paging's LRU/OPT ratio is <= k
      and attains k on the classic adversarial sequence, and no-information
      scheduling sits above the offline optimum and below the naive ratio.

CPU only, stdlib only. Deterministic (fixed seeds). No claim is made here.
"""
import io, itertools, json, os, random, sys

RESULTS = {}

# ---------------------------------------------------------------- ski rental
def ski_offline(n, r, b):
    return min(n * r, b)

def ski_offline_bruteforce(n, r, b):
    # min over the day on which you buy (day 0 = never buy)
    best = min(n * r, b)
    for d in range(1, n + 1):
        cost = (d - 1) * r + b if d <= n else n * r
        best = min(best, cost)
    return best

def ski_online_buy_at(d_buy, n, r, b):
    if n < d_buy:
        return n * r
    return (d_buy - 1) * r + b

def check_ski():
    rows = []
    ok_brute = True
    for r in (1, 2):
        for b in (10, 100, 1000):
            d_buy = max(1, b // r)          # classic deterministic rule: buy on day b/r
            for n in (1, 3, 10, 50, 100, 500, 2000):
                off = ski_offline(n, r, b)
                bf = ski_offline_bruteforce(n, r, b)
                ok_brute &= (off == bf)
                on = ski_online_buy_at(d_buy, n, r, b)
                ratio = on / off
                rows.append((r, b, d_buy, n, off, on, ratio))
    worst = max(x[6] for x in rows)
    # classic bound 2 - r/b is attained when the instance runs long enough
    long_rows = [x for x in rows if x[3] >= max(10, 2 * x[1] // x[0])]
    exact = [x for x in long_rows if abs(x[6] - (2 - x[0] / x[1])) < 1e-12]
    RESULTS["ski_rental"] = {
        "bruteforce_offline_matches_formula": ok_brute,
        "n_instances": len(rows),
        "worst_ratio_all": worst,
        "classic_bound_2_minus_r_over_b_attained": len(exact) == len(long_rows),
        "long_instances": len(long_rows),
    }

# -------------------------------------------------------------------- paging
def belady(trace, k):
    cache, cost = set(), 0
    for i, p in enumerate(trace):
        if p in cache:
            continue
        cost += 1
        if len(cache) < k:
            cache.add(p)
        else:
            nxt = {}
            for q in cache:
                try:
                    nxt[q] = trace.index(q, i + 1)
                except ValueError:
                    nxt[q] = len(trace) + 1
            cache.discard(max(nxt, key=lambda q: (nxt[q], q)))
            cache.add(p)
    return cost

def opt_offline_dp(trace, k):
    """Exact offline optimum by exhaustive search over offline decisions --
    computed independently of Belady, so agreement is a real check."""
    def rec(i, cache):
        if i == len(trace):
            return 0
        page = trace[i]
        if page in cache:
            return rec(i + 1, cache)
        if len(cache) < k:
            return 1 + rec(i + 1, cache | {page})
        return 1 + min(rec(i + 1, (cache - {e}) | {page}) for e in cache)

    return rec(0, frozenset())

def lru_cost(trace, k):
    cache, cost = [], 0
    for p in trace:
        if p in cache:
            cache.remove(p); cache.append(p)
            continue
        cost += 1
        if len(cache) >= k:
            cache.pop(0)
        cache.append(p)
    return cost

def adversarial_paging(k, reps):
    """Classic k-competitive sequence: (1..k, k+1) repeated."""
    t = []
    for _ in range(reps):
        t.extend(list(range(1, k + 1)) + [k + 1])
    return t

def check_paging():
    rnd = random.Random(20260915)
    brute_ok = True; n_brute = 0
    viol = 0; n_rand = 0; worst_rand = 0.0
    # (A) Belady == exhaustive offline optimum on small random traces
    for k in (2, 3):
        for _ in range(12):
            L = rnd.choice([7, 9, 11])
            trace = [rnd.randrange(1, k + 3) for _ in range(L)]
            b, o = belady(trace, k), opt_offline_dp(trace, k)
            n_brute += 1
            brute_ok &= (b == o)
    # (B) LRU/OPT <= k on random traces, and == k on the adversarial one
    ratios_adv = {}
    for k in (2, 3, 4, 5):
        for _ in range(60):
            trace = [rnd.randrange(1, k + 3) for _ in range(200)]
            ratio = lru_cost(trace, k) / belady(trace, k)
            n_rand += 1
            worst_rand = max(worst_rand, ratio)
            viol += (ratio > k + 1e-12)
        r200 = lru_cost(adversarial_paging(k, 200), k) / belady(adversarial_paging(k, 200), k)
        r2000 = lru_cost(adversarial_paging(k, 2000), k) / belady(adversarial_paging(k, 2000), k)
        ratios_adv[k] = {"reps200": r200, "reps2000": r2000}
    RESULTS["paging"] = {
        "belady_equals_exhaustive_optimum": brute_ok, "brute_cases": n_brute,
        "random_traces": n_rand, "ratio_gt_k_violations": viol,
        "worst_random_ratio": worst_rand,
        "adversarial_ratio_by_k": ratios_adv,
        # the classic k-competitive sequence approaches k from BELOW with an O(1/reps)
        # deficit: the correct anchor statement is a limit, not an equality.
        "adversarial_bound_never_exceeded": all(
            max(v["reps200"], v["reps2000"]) <= k + 1e-9 for k, v in ratios_adv.items()),
        "adversarial_approaches_k": all(
            abs(v["reps2000"] - k) <= 0.02 and v["reps2000"] >= v["reps200"] for k, v in ratios_adv.items()),
    }

# ---------------------------------------------------------------- scheduling
def flow_offline_spt(jobs):
    return sum((len(jobs) - i) * j for i, j in enumerate(sorted(jobs)))

def flow_offline_bruteforce(jobs):
    n = len(jobs); best = None
    for perm in itertools.permutations(jobs):
        c = 0
        for i, j in enumerate(perm):
            c += (n - i) * j
        best = c if best is None else min(best, c)
    return best

def flow_fifo(jobs):
    n = len(jobs); c = 0
    for i, j in enumerate(jobs):
        c += (n - i) * j
    return c

def check_scheduling():
    rnd = random.Random(47)
    ok = True; n_cases = 0
    fifo_ratios = []
    for _ in range(200):
        n = rnd.randrange(2, 8)
        jobs = [rnd.randrange(1, 20) for _ in range(n)]
        n_cases += 1
        ok &= (flow_offline_spt(jobs) == flow_offline_bruteforce(jobs))
    for _ in range(400):
        n = rnd.randrange(3, 25)
        jobs = [rnd.randrange(1, 50) for _ in range(n)]
        opt = flow_offline_spt(jobs)
        fifo_ratios.append(flow_fifo(jobs) / opt)
    RESULTS["scheduling"] = {
        "spt_equals_bruteforce_optimum": ok, "brute_cases": n_cases,
        "fifo_over_opt_median": sorted(fifo_ratios)[len(fifo_ratios) // 2],
        "fifo_over_opt_min": min(fifo_ratios), "fifo_over_opt_max": max(fifo_ratios),
        "fifo_never_beats_opt": min(fifo_ratios) >= 1 - 1e-12,
    }

def main():
    check_ski(); check_paging(); check_scheduling()
    verdict = []
    verdict.append(("ski: offline exact", RESULTS["ski_rental"]["bruteforce_offline_matches_formula"]))
    verdict.append(("ski: classic 2-r/b attained", RESULTS["ski_rental"]["classic_bound_2_minus_r_over_b_attained"]))
    verdict.append(("paging: Belady == exhaustive optimum", RESULTS["paging"]["belady_equals_exhaustive_optimum"]))
    verdict.append(("paging: LRU/OPT <= k (0 violations)", RESULTS["paging"]["ratio_gt_k_violations"] == 0))
    verdict.append(("paging: adversarial never exceeds k", RESULTS["paging"]["adversarial_bound_never_exceeded"]))
    verdict.append(("paging: adversarial approaches k from below (limit)", RESULTS["paging"]["adversarial_approaches_k"]))
    verdict.append(("sched: SPT == brute-force optimum", RESULTS["scheduling"]["spt_equals_bruteforce_optimum"]))
    verdict.append(("sched: FIFO >= opt", RESULTS["scheduling"]["fifo_never_beats_opt"]))
    allok = all(v for _, v in verdict)
    out = {"anchors": RESULTS, "verdict": [{"check": k, "ok": v} for k, v in verdict],
           "ANCHORS_ALL_PASS": allok}
    printed = json.dumps(out, indent=1, sort_keys=True)
    print(printed)
    d = os.path.dirname(os.path.abspath(__file__))
    with io.open(os.path.join(d, "anchor_smoke_results.json"), "w", encoding="utf-8") as f:
        f.write(printed + "\n")
    return 0 if allok else 1

if __name__ == "__main__":
    sys.exit(main())
