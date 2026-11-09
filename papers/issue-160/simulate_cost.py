# -*- coding: utf-8 -*-
"""simulate_cost.py -- the check registered criterion (ii) asked for, on the law section 6 states.

Criterion (ii) reads: *"the cost law's prediction is checked against an exact simulation on the real
empirical distributions, with the residual stated."* Until the revision round that criterion was
reported UNMET, and it was unmet: `K = ceil(log R / log(1+eps))` was evaluated over real `R` values
and never compared against a procedure actually run on the rows. This module runs it.

WHAT THE LAW CLAIMS, AND WHAT CHECKING IT MEANS
-----------------------------------------------
The law prices a certification: pinning the q-quantile to relative precision `eps` using timeout
levels alone costs `K` distinct levels. A certification by levels works by placing timeouts and
reading which side of each one the quantile falls on, so the precision it reaches is the width of
the interval between the two levels that bracket the quantile. Checking the law therefore means
placing `K` levels, measuring the bracket width achieved on each row's own reconstructed
distribution, and comparing that width against `eps`. The **residual** is the achieved width divided
by `eps`: at or below 1 the law's price buys the precision it claims, above 1 it does not.

This is measured, not assumed, because the quantile sits at a different position inside the grid on
every row: the achieved width is an empirical quantity over 47,502 ladders, not an algebraic
identity in `R`.

It is run at three level counts -- `K-1`, `K` and `K+1` -- because the answer decides what the law
may be stated as:
  * if `K` levels attain `eps` on every row, the law as written is right;
  * if `K+1` is needed, the law's `K` counts the number of GAPS and not the number of LEVELS, and
    the sentence in section 6 has to say which it is selling;
  * if `K-1` already attains `eps`, the law over-prices the certification by a level, and that is a
    result rather than a defect -- it would mean the third headline number is too high.

A separate limb checks the reconstruction itself, because every number above rides on it: invocations
are drawn from each row's own reconstructed distribution and their empirical q-quantile is compared
against the ladder's. That limb is a check of the interpolation, not of the law, and it is labelled
as such -- mixing the two would let a level failure be read as an interpolation artefact.

Determinism: no clock, no environment, and the draws use a fixed seed, so `results/crossover.json`
still regenerates byte-identically.
"""
import math
import random

import censored_tail as ct

EPS_GRID = (0.05, 0.10, 0.20)
# Reconstruction limb: a fixed stride and fixed seed, so this is reproducible rather than a sample
# whose result moves between runs.
RECON_ROWS = 200
RECON_DRAWS = 512
RECON_SEED = 20261110


def _pctl(xs, p):
    """Linear-interpolation percentile of a plain list. Deterministic; no library dependency."""
    if not xs:
        return None
    s = sorted(xs)
    if len(s) == 1:
        return s[0]
    pos = p * (len(s) - 1)
    lo = int(pos)
    hi = min(lo + 1, len(s) - 1)
    return s[lo] + (s[hi] - s[lo]) * (pos - lo)


def levels(p50, p100, m):
    """`m` timeout levels placed geometrically across the row's own empirical range.

    The range the law prices is `R = p100/p50`, so the levels span exactly that and no more: a
    construction spanning more would be charged for range the law never claimed to cover, and one
    spanning less would credit it with precision it never paid for.
    """
    if m <= 1:
        return [p100]
    g = (p100 / p50) ** (1.0 / (m - 1))
    return [p50 * (g ** i) for i in range(m)]


def bracket(levels_, v):
    """The level interval containing `v`, and its relative width.

    A quantile below the first level is clamped into the first interval: levels that start at the
    median do not resolve anything below the median either, and pretending they do would credit the
    construction with resolution it does not have.
    """
    if len(levels_) >= 2:
        if v <= levels_[0]:
            return (levels_[1] - levels_[0]) / levels_[0]
        for lo, hi in zip(levels_, levels_[1:]):
            if lo <= v <= hi:
                return (hi - lo) / lo
        lo, hi = levels_[-2], levels_[-1]
        return (hi - lo) / lo
    return 0.0


def bracket_at(levels_, v, span):
    """Width actually achieved, with the one-level case treated as what it is.

    A single timeout level has no interval to bracket the quantile in, so the precision it reaches is
    the whole range and not zero. The first version of this function returned 0.0 here -- a single
    level credited with perfect resolution -- and the selftest caught it by failing the plant that
    was supposed to prove the check can fire. A guard that reports the degenerate case as ideal
    verifies the law precisely where the law is weakest.
    """
    if len(levels_) < 2:
        return span
    return bracket(levels_, v)


def law_at(kept, q, eps, extra):
    """Achieved bracket width per row when the level count is `K + extra`."""
    widths, counts = [], []
    for row in kept:
        pts = row["pts"]
        K = ct.levels_needed(row["R"], eps)
        m = K + extra
        if m < 1:
            m = 1
        p50, p100 = ct.quantile(pts, 0.5), ct.quantile(pts, 1.0)
        v = ct.quantile(pts, q)
        span = (p100 - p50) / p50 if p50 else 0.0
        widths.append(bracket_at(levels(p50, p100, m), v, span))
        counts.append(m)
    over = sum(1 for w in widths if w > eps * (1.0 + 1e-12))
    return dict(
        extra_levels=extra,
        levels_median=int(_pctl(counts, 0.5)),
        levels_p90=int(_pctl(counts, 0.9)),
        levels_max=int(max(counts)),
        achieved_median=round(_pctl(widths, 0.5), 6),
        achieved_p90=round(_pctl(widths, 0.9), 6),
        achieved_max=round(max(widths), 6),
        # The residual, which is what criterion (ii) asked to be stated: achieved precision against
        # the precision the law promises. It is reported on the median row and on the worst row,
        # because a price that buys the precision typically but not always is not a certification.
        residual_median=round(_pctl(widths, 0.5) / eps, 4),
        residual_max=round(max(widths) / eps, 4),
        rows_over_eps=over,
        rows=len(widths),
        rows_over_eps_frac=round(over / float(len(widths)), 4),
    )


def reconstruction(kept, q):
    """Do draws from each row's own distribution reproduce the ladder's quantile?

    A stride over the usable rows rather than a random sample, plus a fixed seed: this limb exists to
    show the interpolation is not inventing the tail, and a check whose rows move between runs
    cannot be byte-compared.
    """
    rng = random.Random(RECON_SEED)
    stride = max(1, len(kept) // RECON_ROWS)
    picked = kept[::stride][:RECON_ROWS]
    rel = []
    for row in kept_stride_safe(picked):
        pts = row["pts"]
        v = ct.quantile(pts, q)
        if v <= 0:
            continue
        draws = []
        for _ in range(RECON_DRAWS):
            draws.append(ct.quantile(pts, rng.random()))
        draws.sort()
        pos = q * (len(draws) - 1)
        lo = int(pos)
        hi = min(lo + 1, len(draws) - 1)
        est = draws[lo] + (draws[hi] - draws[lo]) * (pos - lo)
        rel.append(abs(est - v) / v)
    return dict(rows=len(rel), draws_per_row=RECON_DRAWS, seed=RECON_SEED,
                rel_err_median=round(_pctl(rel, 0.5), 6),
                rel_err_p90=round(_pctl(rel, 0.9), 6),
                rel_err_max=round(max(rel), 6),
                note=("draw-based check of the piecewise-linear reconstruction: how far the "
                      "empirical q-quantile of drawn invocations sits from the ladder's own "
                      "quantile. Sampling error at this draw count is the floor here; this limb "
                      "tests the interpolation, NOT the cost law."))


def kept_stride_safe(rows):
    """Iterate without assuming a list -- `kept` may be a generator in a caller's refactor."""
    for r in rows:
        yield r


def check(kept, q, eps_grid=EPS_GRID):
    """The block stored in `results/crossover.json` under `cost_check`."""
    eps_blocks = {}
    for eps in eps_grid:
        tag = "%d" % int(eps * 100)
        eps_blocks["eps_" + tag] = dict(
            eps=eps,
            at_K_minus_1=law_at(kept, q, eps, -1),
            at_K=law_at(kept, q, eps, 0),
            at_K_plus_1=law_at(kept, q, eps, +1),
        )
    # The verdict sentence, as data: which level count attains eps on EVERY row at every eps. A law
    # stated with one level too few is a law whose price does not buy its product, and the artefact
    # should say which it is rather than leaving it to a reader to read off two rows of a table.
    holds_at = {}
    for tag, blk in sorted(eps_blocks.items()):
        for key in ("at_K_minus_1", "at_K", "at_K_plus_1"):
            if blk[key]["rows_over_eps"] == 0:
                holds_at[tag] = key
                break
        else:
            holds_at[tag] = "none_of_the_three"
    return dict(
        criterion="registered success criterion (ii): the cost law's prediction checked against "
                  "the empirical distributions, with the residual stated",
        construction=("levels placed geometrically across each row's own [p50, p100], the range "
                      "R = p100/p50 the law prices; achieved precision = relative width of the "
                      "level interval bracketing the row's own q-quantile"),
        residual_definition="achieved relative bracket width / eps; <= 1 means the law's price "
                            "buys the precision it claims",
        holds_at=holds_at,
        by_eps=eps_blocks,
        reconstruction=reconstruction(kept, q),
        unit="interval mean (30-s average), NOT single invocations -- trace footnote 7",
    )


def selftest():
    """A check nobody has seen fail is not a check.

    The plants are the two ways this one can be wrong: a law that charges one level too few (the
    residual must exceed 1 on some rows, so the gate that reads it must be able to fire) and a law
    that charges one too many (the residual must be below 1 everywhere, so a gate asserting `> 1`
    would be red). Both are built from real-shaped rows, and the arithmetic is the same arithmetic
    the real run uses -- not a copy of it.
    """
    fails = 0

    def expect(name, ok, detail=""):
        nonlocal fails
        print("  [%s] %s%s" % ("ok" if ok else "FAIL", name, (" -- " + detail) if detail else ""))
        if not ok:
            fails += 1

    # a row with a wide range: R = 100, eps = 5% -> the law charges K = ceil(log100/log1.05) = 93
    pts = [(0.0, 1.0), (0.01, 1.2), (0.25, 60.0), (0.5, 100.0), (0.75, 140.0),
           (0.99, 200.0), (1.0, 10000.0)]
    row = dict(pts=pts, R=100.0)
    eps = 0.05

    under = law_at([row], 0.99, eps, 0)
    plus = law_at([row], 0.99, eps, +1)
    minus = law_at([row], 0.99, eps, -1)
    expect("the law's own level count is evaluated, not assumed",
           under["levels_median"] == ct.levels_needed(100.0, eps),
           "K=%d" % under["levels_median"])
    expect("adding a level never widens the achieved bracket",
           plus["achieved_max"] <= under["achieved_max"] + 1e-12 and
           under["achieved_max"] <= minus["achieved_max"] + 1e-12,
           "K-1 %.6f | K %.6f | K+1 %.6f"
           % (minus["achieved_max"], under["achieved_max"], plus["achieved_max"]))

    # plant 1: the law's own level count must be refusable by the predicate the gate uses. On a row
    # whose range spans two decades, `K` levels leave `K-1` gaps, and `R**(1/(K-1)) - 1` exceeds eps
    # -- which is the whole question this module exists to settle.
    expect("the law's own level count leaves a bracket wider than eps (under-priced by one level)",
           under["residual_max"] > 1.0 and under["rows_over_eps"] > 0,
           "K=%d achieved=%.6f residual=%.4f rows_over=%d"
           % (under["levels_median"], under["achieved_max"], under["residual_max"],
              under["rows_over_eps"]))
    expect("and the level count that does buy eps is the law's K plus one",
           plus["residual_max"] <= 1.0 and plus["rows_over_eps"] == 0,
           "K+1=%d achieved=%.6f residual=%.4f"
           % (plus["levels_median"], plus["achieved_max"], plus["residual_max"]))

    # plant 2: the predicate is not simply always true -- a count that buys the precision is not
    # flagged, and one level below the law is flagged harder than the law itself.
    expect("one level below the law is flagged at least as hard as the law",
           minus["residual_max"] >= under["residual_max"] - 1e-12,
           "K-1 residual %.4f vs K residual %.4f" % (minus["residual_max"], under["residual_max"]))

    # plant 3: the degenerate endpoint. R = 1 is a flat workload: one level, zero width, residual 0.
    flat = dict(pts=[(0.0, 5.0), (0.01, 5.0), (0.25, 5.0), (0.5, 5.0), (0.75, 5.0),
                     (0.99, 5.0), (1.0, 5.0)], R=1.0)
    zero = law_at([flat], 0.99, 0.05, 0)
    expect("a flat workload is certified by one level at zero width",
           zero["levels_median"] == 1 and zero["achieved_max"] == 0.0 and zero["residual_max"] == 0.0,
           "levels=%d achieved=%.6f" % (zero["levels_median"], zero["achieved_max"]))

    # plant 4: the reconstruction limb must see a distribution it was handed, not an empty list.
    rec = reconstruction([row, row], 0.99)
    expect("the reconstruction limb actually drew and measured",
           rec["rows"] > 0 and rec["rel_err_median"] is not None,
           "rows=%d median rel err %.6f" % (rec["rows"], rec["rel_err_median"] or -1))

    print("SELFTEST: %s" % ("PASS" if fails == 0 else "%d FAILED" % fails))
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    import sys
    sys.exit(selftest())
