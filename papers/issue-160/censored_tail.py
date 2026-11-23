# -*- coding: utf-8 -*-
"""censored_tail.py -- what a timeout leaves identifiable about a tail quantile.

Pure functions, no I/O, so every claim can be re-derived and every refusal can be tested.

THE OBJECT. A harness observes a request or stops waiting at a timeout `T`; a request that times out
has no latency value. Write `c` for the fraction that times out and `F` for the latency CDF. The
harness's sample is `X | X <= T`, whose CDF is `F(x)/F(T)` on `[0, T]`.

THE LEMMA (not a measurement). The true `q`-quantile is identified by the harness exactly when
`q <= F(T)`, i.e. exactly when `c <= 1 - q`. When `c > 1 - q` the true quantile lies strictly above
`T` and the harness cannot place it: the identified set is `(T, inf)`, unbounded above, and no volume
of traffic narrows it -- the missing mass is missing, not noisy. What the harness *reports* in that
case is the `q`-quantile of the truncated sample, `Q(q * F(T))`, which is strictly below `T` and
therefore strictly below the truth.

THE UNITS. This module takes a *quantile ladder* -- the seven measured percentile points of the
interval-mean latency that the trace publishes. That is the unit of analysis throughout: the trace's
percentile columns are percentiles of a 30-second mean, not of single invocations (dataset footnote
7), so every range computed here is a range of a *smoothed* distribution and is a LOWER bound on the
invocation-level range.

THE COST LAW. Certifying a quantile to relative precision `eps` by timeout levels alone needs
`K = ceil(log(R) / log(1 + eps))` distinct levels, where `R` is the dynamic range the ladder spans.
It dies at `R = 1` (a flat workload needs one level) -- that is its degenerate endpoint, and the
selftest evaluates it there.
"""
import math

# The seven ladder knots, as (probability, column) in ascending order. The names are the trace's.
LADDER = [(0.00, "percentile_Average_0"),
          (0.01, "percentile_Average_1"),
          (0.25, "percentile_Average_25"),
          (0.50, "percentile_Average_50"),
          (0.75, "percentile_Average_75"),
          (0.99, "percentile_Average_99"),
          (1.00, "percentile_Average_100")]


def ladder_points(row):
    """(u, value) knots for one trace row, or None when the ladder is not usable.

    A row is usable only if its ladder is non-decreasing in `u` and its median is positive: a row
    whose knots cross is a recording defect, not a distribution, and interpolating through it would
    invent tail mass. Refusing them is the point -- the count of refusals is reported.
    """
    pts, prev = [], -1.0
    for u, col in LADDER:
        try:
            v = float(row[col])
        except (KeyError, TypeError, ValueError):
            return None
        if v != v or v < 0:                                  # NaN or negative
            return None
        if v < prev:                                         # ladder crosses: refuse
            return None
        pts.append((u, v))
        prev = v
    if pts[3][1] <= 0.0:                                     # median must be positive
        return None
    return pts


def quantile(pts, u):
    """Piecewise-linear inverse CDF at `u`. The reconstruction, stated as one."""
    if u <= 0.0:
        return pts[0][1]
    if u >= 1.0:
        return pts[-1][1]
    for (u0, v0), (u1, v1) in zip(pts, pts[1:]):
        if u0 <= u <= u1:
            if u1 == u0:
                return v1
            return v0 + (v1 - v0) * (u - u0) / (u1 - u0)
    return pts[-1][1]


def cdf(pts, x):
    """F(x) by inverting the same piecewise-linear ladder -- the same reconstruction, read backwards."""
    if x <= pts[0][1]:
        return 0.0
    if x >= pts[-1][1]:
        return 1.0
    for (u0, v0), (u1, v1) in zip(pts, pts[1:]):
        if v0 <= x <= v1:
            if v1 == v0:
                return u1
            return u0 + (u1 - u0) * (x - v0) / (v1 - v0)
    return 1.0


def censored_fraction(pts, T):
    """`c`: the fraction of the distribution strictly above the timeout."""
    return 1.0 - cdf(pts, T)


def identified(q, c):
    """Is the true q-quantile identified by a harness that censors a fraction `c`? (the lemma)"""
    return c <= 1.0 - q


def reported_quantile(pts, q, T):
    """What the harness prints: the q-quantile of the truncated sample, `Q(q * F(T))`."""
    return quantile(pts, q * cdf(pts, T))


def identified_set(pts, q, T):
    """(reported, lo, hi): the printed number and the set the true quantile may occupy.

    When identified the set is the single point `reported == true`. When not, it is
    `(T, inf)` -- and `reported` is strictly below `T`, so the harness prints a number below the
    whole set it cannot rule out.
    """
    c = censored_fraction(pts, T)
    rep = reported_quantile(pts, q, T)
    if identified(q, c):
        true = quantile(pts, q)
        return rep, true, true
    return rep, T, math.inf


def levels_needed(R, eps):
    """`K`: timeout levels that certify the quantile to relative precision `eps` over range `R`.

    K = ceil(log R / log(1+eps)); it is 1 when R <= 1, which is the degenerate endpoint: a workload
    with no dynamic range is certified by a single timeout.
    """
    if eps <= 0:
        raise ValueError("eps must be positive")
    if R <= 1.0:
        return 1
    return int(math.ceil(math.log(R) / math.log(1.0 + eps)))


def resolvable(count, q):
    """Can a sample of `count` invocations resolve the q-quantile at all?

    A q-quantile is a statement about the top `1-q` of the distribution; a sample resolves it only
    if it expects at least one observation above it, i.e. `count * (1-q) >= 1`. Below that the
    quantile is an extrapolation from the sample's maximum, whatever the timeout does.
    """
    return count * (1.0 - q) >= 1.0


def observations_above(count, q):
    """Expected number of observations strictly above the q-quantile -- the resolution, stated."""
    return count * (1.0 - q)


def selftest():
    """Every refusal and every endpoint this module can reach, on fixtures small enough to check.

    A guard nobody has seen fail is not a guard, and a formula nobody has evaluated at its known
    answer is a guess. The three endpoints that must hold: no censoring is exact; total censoring is
    unbounded; a flat workload needs one level.
    """
    fails = 0

    def expect(name, ok, detail=""):
        nonlocal fails
        print("  [%s] %s%s" % ("ok" if ok else "FAIL", name, (" -- " + detail) if detail else ""))
        if not ok:
            fails += 1

    # a ladder with a known shape: median 100, p99 200, max 400 (interval-mean latency, ms)
    pts = [(0.0, 10.0), (0.01, 12.0), (0.25, 60.0), (0.5, 100.0), (0.75, 140.0), (0.99, 200.0), (1.0, 400.0)]
    q = 0.99

    # 1. no censoring: the report IS the truth, and the set is a point
    rep, lo, hi = identified_set(pts, q, T=400.0)
    expect("a timeout at the maximum identifies the quantile", identified(q, 0.0) and lo == hi,
           "reported=%.1f set=[%.1f,%.1f]" % (rep, lo, hi))
    expect("and the reported number equals the true one", abs(rep - quantile(pts, q)) < 1e-9,
           "reported=%.4f true=%.4f" % (rep, quantile(pts, q)))

    # 2. the boundary: c == 1-q is still identified (the lemma's closed edge), c slightly above is not
    expect("c exactly 1-q is identified", identified(q, 0.01))
    expect("c just above 1-q is not", not identified(q, 0.0100001))

    # 3. total censoring: unbounded above, and the printed number is BELOW the whole set
    rep2, lo2, hi2 = identified_set(pts, q, T=100.0)
    expect("a median timeout leaves the quantile unidentified", hi2 == math.inf and lo2 == 100.0,
           "set=[%.1f,%s]" % (lo2, "inf" if hi2 == math.inf else "%.1f" % hi2))
    expect("and the harness prints a number below the set it cannot rule out", rep2 < lo2,
           "reported=%.2f < T=%.2f" % (rep2, lo2))

    # 4. the monotone half is a lemma: reported can only rise as T rises. The fixture lists T in
    # ASCENDING order -- the first version listed it descending and asserted an ascending property,
    # so the check failed for the fixture's reason and would have "passed" nowhere.
    reps = [reported_quantile(pts, q, T) for T in (50.0, 100.0, 150.0, 200.0, 300.0, 400.0)]
    expect("reported quantile is monotone non-decreasing in T",
           all(a <= b for a, b in zip(reps, reps[1:])), "reported=%s" % ["%.1f" % r for r in reps])

    # 4b. at the boundary itself the quantile is identified, and the printed number STILL understates:
    # the truncated sample's 99th percentile is the q*F(T)-quantile of the full distribution, so
    # T = p99 prints 0.99*0.99 = 0.9801 of the truth. Being identified is not the same as printing
    # the true value, and this is the case where the two disagree least.
    rep_b, lo_b, hi_b = identified_set(pts, q, T=200.0)
    expect("at T = p99 the quantile is identified, and the printed number still understates it",
           lo_b == hi_b and rep_b < lo_b,
           "reported=%.2f true=%.2f" % (rep_b, lo_b))

    # 5. the cost law, at its degenerate endpoint and at a known value
    expect("a flat workload (R=1) needs exactly one level", levels_needed(1.0, 0.05) == 1)
    expect("R below 1 cannot need fewer than one level", levels_needed(0.5, 0.05) == 1)
    expect("K grows by one per doubling of the range at small eps",
           levels_needed(100.0, 0.05) == int(math.ceil(math.log(100) / math.log(1.05))),
           "K(100,5%%)=%d" % levels_needed(100.0, 0.05))

    # 6. the sample-count limit is separate from the censoring limit
    expect("100 invocations cannot resolve a p99 (expects 1 observation above it)",
           resolvable(100, 0.99) and not resolvable(99, 0.99),
           "count=100 expects %.2f" % observations_above(100, 0.99))
    expect("1000 invocations expect ten observations above p99",
           abs(observations_above(1000, 0.99) - 10.0) < 1e-9)

    # 7. a crossing ladder is refused rather than interpolated
    bad = {"percentile_Average_0": "10", "percentile_Average_1": "12", "percentile_Average_25": "9",
           "percentile_Average_50": "100", "percentile_Average_75": "140",
           "percentile_Average_99": "200", "percentile_Average_100": "400"}
    expect("a ladder whose knots decrease is refused", ladder_points(bad) is None)
    good = {c: str(v) for (_, c), (_, v) in zip(LADDER, pts)}
    expect("a monotone ladder is accepted", ladder_points(good) is not None)
    zero = dict(good); zero["percentile_Average_50"] = "0"
    expect("a row with a zero median is refused", ladder_points(zero) is None)

    print("SELFTEST: %s" % ("PASS" if fails == 0 else "%d FAILED" % fails))
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    import sys
    sys.exit(selftest())
