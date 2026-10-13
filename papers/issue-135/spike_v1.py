#!/usr/bin/env python3
"""Issue #135 -- bounded-scheme probe instrument, v1.

Adds to v0: (a) a ROBIN-HOOD arm, (b) the BUDGET AXIS k_max, (c) the budget
boundary alpha*(k_max) with its mean-based comparison (registered prior P3),
(d) a repaired uniformity certificate (a stated chi-square null instead of v0's
raw max), (e) a per-seed convergence reading instead of v0's mean-over-seeds.

Deterministic, standard-library only, CPU-only, no timings.  Ground truth by
construction: the table state IS the ground truth and every probe is an exact
integer count.  Every reported number is a count, a rate over a named
denominator, or an exact-integer-derived moment.

Scheme definitions (declared, not assumed):
  linear     -- insert by probing h(k), h(k)+1, ... ; lookup probes until the
                first empty slot.  Displacement = insertion probe count.
  robinhood  -- insert by probing; at each slot, if the sitting key's
                displacement is smaller than ours, swap (evict it, continue).
                Run UNBOUNDED here; a bound k_max is then applied to the
                realised displacement distribution (the reading a bound would
                have excluded), which is stated as the definition.

Budget failure, two objects (each rate is over its own denominator):
  lookup_fail(k) = #{ unsuccessful lookups needing > k probes } / #{ lookups }
  insert_fail(k) = #{ stored keys with displacement > k } / #{ stored keys }
alpha*(k) is the load at which a rate crosses a level, by linear interpolation
of log10(rate) on the load grid; 'undef' when the grid does not bracket it.
"""
import json
import math
import sys

MASK = (1 << 64) - 1


class SplitMix64:
    __slots__ = ("s",)

    def __init__(self, seed):
        self.s = seed & MASK

    def next(self):
        self.s = (self.s + 0x9E3779B97F4A7C15) & MASK
        z = self.s
        z = ((z ^ (z >> 30)) * 0xBF58476D1CE4E5B9) & MASK
        z = ((z ^ (z >> 27)) * 0x94D049BB133111EB) & MASK
        return z ^ (z >> 31)


def mixer(key):
    z = key & MASK
    z = ((z ^ (z >> 33)) * 0xFF51AFD7ED558CCD) & MASK
    z = ((z ^ (z >> 33)) * 0xC4CEB9FE1A85EC53) & MASK
    return z ^ (z >> 33)


def identity(key):
    return key & MASK


def key_family(name, n, seed):
    if name == "uniform":
        out = []
        seen = set()
        r = SplitMix64(seed)
        while len(out) < n:
            k = r.next()
            if k not in seen:            # membership only; never iterated
                seen.add(k)
                out.append(k)
        return out
    if name == "sequential":
        base = SplitMix64(seed).next() & 0xFFFF000000000000
        return [base + i for i in range(n)]
    raise ValueError(name)


# ------------------------------------------------------------------ schemes
def build_linear(keys, m, hfn):
    table = [0] * m          # key itself; 0 is never a key (keys are nonzero)
    disp = []
    for key in keys:
        i = hfn(key) % m
        d = 1
        while table[i] != 0:
            i = (i + 1) % m
            d += 1
        table[i] = key
        disp.append(d)       # probes performed (an insertion probe count)
    return table, disp, None


def build_robinhood(keys, m, hfn):
    table = [0] * m
    dist = [-1] * m
    disp = []
    for key in keys:
        i = hfn(key) % m
        cur_key, cur_d = key, 0
        d = 1
        while True:
            if table[i] == 0:
                table[i] = cur_key
                dist[i] = cur_d
                break
            if dist[i] < cur_d:          # swap: the poorer one waits
                table[i], cur_key = cur_key, table[i]
                dist[i], cur_d = cur_d, dist[i]
            i = (i + 1) % m
            cur_d += 1
            d += 1
        disp.append(d)                   # probes performed by THIS insertion
    return table, disp, dist


def longest_run(table, m):
    if 0 not in table:
        return m
    start = table.index(0)
    best = 0
    cur = 0
    for j in range(1, m + 1):
        if table[(start + j) % m] == 0:
            best = max(best, cur)
            cur = 0
        else:
            cur += 1
    return max(best, cur)


def lookup_linear(table, m, key, hfn):
    i = hfn(key) % m
    p = 0
    while True:
        p += 1
        if table[i] == 0:
            return p
        i = (i + 1) % m


def lookup_robinhood(table, dist, m, key, hfn):
    """Robin Hood termination: stop when the sitting key sits closer to its own
    home than we already are (it cannot be ours beyond that point)."""
    i = hfn(key) % m
    p = 0
    d = 0
    while True:
        p += 1
        if table[i] == 0:
            return p
        if dist[i] < d:
            return p
        i = (i + 1) % m
        d += 1


# ------------------------------------------------------------------ helpers
def pct(s, q):
    n = len(s)
    idx = math.ceil(q * n) - 1
    return s[0 if idx < 0 else (n - 1 if idx >= n else idx)]


def chi2_slots(keys, m, hfn):
    """Uniformity certificate with a STATED null: chi-square over m slots.

    Null: n keys independently uniform over m slots -> chi2 ~ chi2_{m-1},
    mean m-1, sd sqrt(2(m-1)); reported as a two-sided z score."""
    counts = [0] * m
    for k in keys:
        counts[hfn(k) % m] += 1
    exp = len(keys) / m
    chi2 = 0.0
    for c in counts:
        chi2 += (c - exp) ** 2 / exp
    z = (chi2 - (m - 1)) / math.sqrt(2 * (m - 1))
    return chi2, z


KMAXES = (2, 4, 8, 16, 32, 64)
PROBE_BUDGET = 4_000_000
MIN_EVENTS = 10       # a rate built from fewer events is NOT a resolved reading
LEVELS = (1e-2, 1e-3, 1e-6)
ALPHAS = (0.01, 0.05, 0.10, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70,
          0.80, 0.85, 0.90, 0.95, 0.99)


def rate_gt(sorted_vals, k):
    """Fraction of values strictly greater than k (exact count / exact n)."""
    lo, hi = 0, len(sorted_vals)
    while lo < hi:                       # first index with val > k
        mid = (lo + hi) // 2
        if sorted_vals[mid] > k:
            hi = mid
        else:
            lo = mid + 1
    return (len(sorted_vals) - lo) / len(sorted_vals)


def run_cell(scheme, family, alpha, seed, m, n_lookups, hash_name):
    hfn = mixer if hash_name == "mixer" else identity
    n = int(round(alpha * m))
    keys = key_family(family, n, seed)
    if scheme == "linear":
        table, disp, dist = build_linear(keys, m, hfn)
        probe = lambda k: lookup_linear(table, m, k, hfn)
    else:
        table, disp, dist = build_robinhood(keys, m, hfn)
        probe = lambda k: lookup_robinhood(table, dist, m, k, hfn)

    chi2, z = chi2_slots(keys, m, hfn)

    # declared sampling rule: draw unsuccessful-search keys until a PROBE
    # budget is spent (bounded runtime), with a hard cap on the draw count.
    # The realised draw count is the rate's denominator and is reported.
    r = SplitMix64(seed ^ 0xABCDEF0123456789)
    look = []
    spent = 0
    while spent < PROBE_BUDGET and len(look) < 300000:
        v = probe(r.next())
        spent += v
        look.append(v)
    look.sort()
    n_lookups = len(look)
    disp_s = sorted(disp)

    tot = 0
    for v in disp_s:
        tot += v
    totl = 0
    for v in look:
        totl += v

    return {
        "scheme": scheme, "family": family, "hash": hash_name, "seed": seed,
        "alpha": alpha, "m": m, "n": n, "n_lookups": n_lookups,
        "chi2": chi2, "chi2_z": z,
        "lookup_mean": totl / n_lookups,
        "lookup_p99": pct(look, 0.99),
        "lookup_p999": pct(look, 0.999),
        "lookup_max": look[-1],
        "disp_mean": tot / n,
        "disp_max": disp_s[-1],
        "longest_run": longest_run(table, m),
        "lookup_fail": {str(k): rate_gt(look, k) for k in KMAXES},
        "insert_fail": {str(k): rate_gt(disp_s, k) for k in KMAXES},
        # event counts, so a 0 is countable and never a bare absence
        "lookup_events": {str(k): sum(1 for v in look if v > k) for k in KMAXES},
    }


# ------------------------------------------------------------------ boundary
def mean_based_load(k):
    """The load at which the CLASSICAL mean equals the budget k:
    U(a) = 0.5 (1 + 1/(1-a)^2) = k  ->  a = 1 - 1/sqrt(2k-1)."""
    return 1.0 - 1.0 / math.sqrt(2.0 * k - 1.0)


def crossing(points, level, events=None):
    """points = [(alpha, rate)] sorted by alpha; first crossing of level from
    below, by linear interpolation in log10(rate).  None when unbracketed."""
    prev = None
    for a, r in points:
        if r <= 0:
            continue
        if r >= level:
            if prev is None:
                # the FIRST drawable load is already above the level: this is a
                # one-sided BOUND, never a measurement (an unresolved cell is
                # not a measured value) -- the floor is reported AS a floor.
                return {"alpha": None, "bracketed": False, "bound": "above",
                        "lower_bound": a,
                        "note": "level already exceeded at the lowest load run; "
                                "alpha* is below the grid floor (a bound, not a value)"}
            pa, pr = prev
            if events is not None:
                # a crossing whose bracketing cells carry < MIN_EVENTS is not a
                # measurement (an unresolved cell is not a measured value)
                if min(events[pa], events[a]) < MIN_EVENTS:
                    return {"alpha": None, "bracketed": False,
                            "bound": "under-resolved",
                            "events": {"lo": events[pa], "hi": events[a]},
                            "note": "bracketing cells carry < MIN_EVENTS events"}
            t = (math.log10(level) - math.log10(pr)) / (math.log10(r) - math.log10(pr))
            return {"alpha": pa + t * (a - pa), "bracketed": True,
                    "lo": pa, "hi": a,
                    "events": None if events is None
                              else {"lo": events[pa], "hi": events[a]}}
        prev = (a, r)
    return {"alpha": None, "bracketed": False, "bound": "below",
            "upper_bound": points[-1][0] if points else None,
            "note": "level not reached on the load grid; alpha* is above the "
                    "grid ceiling (a bound, not a value)"}


def build_grid(scheme, family, seeds=(1, 2, 3), m=16384, n_lookups=50000,
               hash_name="mixer"):
    cells = []
    for alpha in ALPHAS:
        for si, seed in enumerate(seeds):
            s = seed * 1000003 + (0 if family == "uniform" else 777)
            cells.append(run_cell(scheme, family, alpha, s, m, n_lookups, hash_name))
    return cells


def alpha_star(cells, scheme, family, obj, level):
    """alpha*(k_max) for every k_max, seed-averaged, per (scheme, family)."""
    grp = {}
    for c in cells:
        if c["scheme"] != scheme or c["family"] != family:
            continue
        grp.setdefault(c["alpha"], []).append(c)
    alphas = sorted(grp)
    res = {}
    for k in KMAXES:
        pts = []
        ev = {}
        for a in alphas:
            cs = grp[a]
            pts.append((a, sum(c[obj][str(k)] for c in cs) / len(cs)))
            ev[a] = sum(c["lookup_events"][str(k)] for c in cs)
        res[str(k)] = {"crossing": crossing(pts, level, events=ev),
                       "mean_based_load": mean_based_load(k),
                       "events_at_k": ev,
                       "points": [(a, r) for a, r in pts]}
    return res


def mean_load(points, k):
    """The load at which the MEASURED mean equals k (a rising series), by
    linear interpolation; None when unbracketed (stated, not invented)."""
    prev = None
    for a, m in points:
        if m >= k:
            if prev is None:
                return {"alpha": None, "note": "mean already >= k at the lowest "
                        "load run", "upper_bound": a}
            pa, pm = prev
            t = (k - pm) / (m - pm)
            return {"alpha": pa + t * (a - pa), "bracketed": True}
        prev = (a, m)
    return {"alpha": None, "note": "mean never reaches k on the load grid",
            "upper_bound": points[-1][0] if points else None}


def mean_series(cells, scheme, family, obj_mean="lookup_mean"):
    grp = {}
    for c in cells:
        if c["scheme"] != scheme or c["family"] != family or c["hash"] != "mixer":
            continue
        grp.setdefault(c["alpha"], []).append(c[obj_mean])
    return [(a, sum(v) / len(v)) for a, v in sorted(grp.items())]


# ------------------------------------------------------------------ checks
def build_all(m=16384, n_lookups=50000):
    cells = []
    for scheme in ("linear", "robinhood"):
        for family in ("uniform", "sequential"):
            cells += build_grid(scheme, family, m=m, n_lookups=n_lookups)
    plant = []
    for scheme in ("linear", "robinhood"):
        plant += build_grid(scheme, "sequential", m=m, n_lookups=n_lookups,
                            hash_name="plant")
    return cells, plant


def checks(cells, plant):
    out = {}

    # C4 (repaired) -- uniformity certificate with a STATED null, two-sided.
    zs = {}
    for c in cells:
        zs.setdefault(c["scheme"], []).append(abs(c["chi2_z"]))
    pz = [abs(c["chi2_z"]) for c in plant]
    # the certificate is NOT load-invariant: at low load EVERY layout gives
    # chi2 ~ m (most slots are empty), so its power vanishes.  Report power
    # per load and restrict any separation claim to the power window.
    power = {}
    for a in ALPHAS:
        mz = [abs(c["chi2_z"]) for c in cells if c["alpha"] == a]
        pz_a = [abs(c["chi2_z"]) for c in plant if c["alpha"] == a]
        if not mz or not pz_a:
            continue
        power["%.2f" % a] = {"mixer_max_abs_z": max(mz),
                             "plant_min_abs_z": min(pz_a),
                             "separates": min(pz_a) > max(mz)}
    window = sorted(float(k) for k, v in power.items() if v["separates"])
    out["C4_uniformity_chi2"] = {
        "null": "chi2 ~ chi2_{m-1}; z = (chi2-(m-1))/sqrt(2(m-1))",
        "mixer_max_abs_z": max(max(v) for v in zs.values()),
        "plant_min_abs_z": min(pz) if pz else None,
        "separates_overall": (min(pz) > max(max(v) for v in zs.values())) if pz else None,
        "separation_window_alpha": window,
        "power_by_load": power,
        "finding": "the certificate's POWER depends on the load: at low load "
                   "chi2 ~ m for every layout (most slots empty), so a clustered "
                   "table is indistinguishable from a uniform one there",
    }

    # C5 (repaired) -- per-seed convergence: report the deviations, no false claim
    devs = {}
    for c in cells:
        if c["hash"] != "mixer":
            continue
        f = 0.5 * (1.0 + 1.0 / (1.0 - c["alpha"]) ** 2)
        devs.setdefault("%s|%.2f" % (c["scheme"], c["alpha"]), []).append(
            (c["lookup_mean"] - f) / f)
    out["C5_seed_convergence"] = {
        "note": "per-seed relative deviation of the mean vs the classical U(a); "
                "reported, not asserted monotone (v0 showed why)",
        "cells": {k: [round(x, 4) for x in v] for k, v in sorted(devs.items())},
    }

    # C7 -- the budget boundary (P3): alpha*(k) vs the mean-based load
    P3 = {}
    for scheme in ("linear", "robinhood"):
        for family in ("uniform", "sequential"):
            mser = mean_series(cells, scheme, family, "lookup_mean")
            for obj in ("lookup_fail", "insert_fail"):
                a = alpha_star(cells, scheme, family, obj, 1e-3)
                rows = {}
                for k in KMAXES:
                    e = a[str(k)]
                    cr = e["crossing"]
                    mb = e["mean_based_load"]
                    ml = mean_load(mser, k)
                    rows[str(k)] = {
                        "events_at_k": a[str(k)]["events_at_k"],
                        "alpha_star": cr.get("alpha"),
                        "bracketed": cr.get("bracketed"),
                        "note": cr.get("note"),
                        "bound": cr.get("bound"),
                        "formula_mean_load": mb,
                        "measured_mean_load": ml.get("alpha"),
                        "measured_mean_note": ml.get("note"),
                        "gap_vs_formula": (mb - cr["alpha"])
                            if cr.get("alpha") is not None else None,
                        "gap_vs_measured_mean": (ml["alpha"] - cr["alpha"])
                            if (cr.get("alpha") is not None
                                and ml.get("alpha") is not None) else None,
                    }
                P3["%s|%s|%s" % (scheme, family, obj)] = rows
    out["C7_budget_boundary"] = P3

    # C8 -- two-sided control: alpha* must be INCREASING in k_max
    ctrl = {}
    for key, rows in P3.items():
        vals = [rows[str(k)]["alpha_star"] for k in KMAXES
                if rows[str(k)]["alpha_star"] is not None]
        ctrl[key] = {
            "monotone_increasing": all(vals[i] < vals[i + 1] for i in range(len(vals) - 1))
            if len(vals) > 1 else None,
            "n_resolved": len(vals), "n_unbracketed": len(KMAXES) - len(vals),
            "ns": [rows[str(k)]["alpha_star"] for k in KMAXES],
        }
    out["C8_budget_control"] = ctrl

    # C10 -- the classical formula is a statement about ONE scheme: report each
    # scheme's deviation, with its across-seed spread (the linear arm is noisy,
    # the Robin Hood arm is tight -- that difference IS a finding)
    dev = {}
    for c in cells:
        if c["hash"] != "mixer":
            continue
        f = 0.5 * (1.0 + 1.0 / (1.0 - c["alpha"]) ** 2)
        dev.setdefault("%s|%.2f" % (c["scheme"], c["alpha"]), []).append(
            (c["lookup_mean"] - f) / f)
    out["C10_deviation_from_linear_formula"] = {
        k: {"mean": round(sum(v) / len(v), 4),
            "spread": round(max(v) - min(v), 4), "n": len(v)}
        for k, v in sorted(dev.items())}

    # C9 -- the budget check's PLANT: a bad layout must cross the budget EARLIER
    plant_first = {}
    for scheme in ("linear", "robinhood"):
        a = alpha_star(plant, scheme, "sequential", "lookup_fail", 1e-3)
        v = [a[str(k)]["crossing"].get("alpha") for k in KMAXES]
        plant_first[scheme] = [None if x is None else round(x, 4) for x in v]
    out["C9_budget_plant"] = plant_first
    return out


# ---------------------------------------------------------------- output path
def out_path(default):
    """Where the report is written.  SPIKE_OUT overrides it, so reproduce.sh can
    run the instrument with the package left untouched (it writes into a private
    temp dir and compares)."""
    import os
    return os.environ.get("SPIKE_OUT", default)


def main():
    cells, plant = build_all()
    report = {"instrument": "spike_v1", "issue": 135,
              "schemes": ["linear", "robinhood"], "alphas": list(ALPHAS),
              "kmaxes": list(KMAXES), "levels": list(LEVELS),
              "cells": cells + plant,
              "checks": checks(cells, plant)}
    with open(out_path("spike_v1_results.json"), "w") as fh:
        fh.write(json.dumps(report, sort_keys=True, indent=1))
    return report



# ---------------------------------------------------------------- selftest
def selftest():
    """Plant battery.  Every plant must FIRE; every pure function is checked
    against an independently computed value."""
    ok, miss = [], []

    def want(name, cond):
        (ok if cond else miss).append(name)

    # rate_gt is an exact count/exact n ratio (binary search, not a scan)
    want("rate_gt_exact", abs(rate_gt(sorted([1, 2, 3, 9]), 2) - 2 / 4) < 1e-15)
    want("rate_gt_strict", abs(rate_gt(sorted([1, 2, 3]), 1) - 2 / 3) < 1e-15)
    want("rate_gt_none", rate_gt(sorted([1, 2, 3]), 9) == 0.0)
    want("rate_gt_all", rate_gt(sorted([9, 9]), 1) == 1.0)

    # the classical mean-based load, an independently written expression
    want("mean_based_load_k8",
         abs(mean_based_load(8) - (1 - 1 / (2 * 8 - 1) ** 0.5)) < 1e-15)

    # crossing: a bracketed series gives the interpolated load
    pts = [(0.10, 1e-6), (0.20, 1e-2)]
    cr = crossing(pts, 1e-3)
    t = (math.log10(1e-3) - math.log10(1e-6)) / (math.log10(1e-2) - math.log10(1e-6))
    want("crossing_interpolates", cr["bracketed"] and abs(cr["alpha"] - (0.10 + t * 0.10)) < 1e-12)
    # an END-POINT crossing is a BOUND, never a value (Class 206c)
    cr2 = crossing([(0.10, 1e-2), (0.20, 1e-1)], 1e-3)
    want("crossing_endpoint_is_a_bound",
         cr2["alpha"] is None and cr2["bound"] == "above")
    # the MIN_EVENTS guard: a crossing on 1-event cells is not a measurement
    cr3 = crossing([(0.10, 1e-6), (0.20, 1e-2)], 1e-3, events={0.10: 1, 0.20: 2})
    want("crossing_underrresolved_guard",
         cr3["alpha"] is None and cr3["bound"] == "under-resolved")
    cr4 = crossing([(0.10, 1e-6), (0.20, 1e-2)], 1e-3, events={0.10: 50, 0.20: 60})
    want("crossing_resolved_passes", cr4["bracketed"])

    # mean_load solves mean_measured(a) = k on a synthetic rising series
    ml = mean_load([(0.10, 1.0), (0.20, 3.0)], 2.0)
    want("mean_load_interpolates", abs(ml["alpha"] - 0.15) < 1e-12)

    # the Robin Hood invariant: the stored displacement is (slot - home) mod m
    keys = key_family("uniform", 200, 5)
    table, disp, dist = build_robinhood(keys, 512, mixer)
    inv = all(dist[i] == (i - mixer(x) % 512) % 512
              for i, x in enumerate(table) if x != 0)
    want("robinhood_displacement_invariant", inv)
    # and every stored key is findable by the Robin Hood lookup (a broken early
    # exit would drop keys silently)
    found = 0
    for k in keys:
        i, d = mixer(k) % 512, 0
        while True:
            if table[i] == k:
                found += 1
                break
            if table[i] == 0 or dist[i] < d:
                break
            i, d = (i + 1) % 512, d + 1
    want("robinhood_finds_every_key", found == len(keys))

    # PLANT: linear and Robin Hood fill the SAME slots -- the invariance the
    # manuscript's C14 rests on.  If this ever failed, C14's finding would be an
    # artefact of the builder rather than of the schemes.
    tl, _, _ = build_linear(keys, 512, mixer)
    occl = [i for i, x in enumerate(tl) if x != 0]
    occr = [i for i, x in enumerate(table) if x != 0]
    want("plant_same_occupied_set", occl == occr)

    print("SELFTEST %d/%d" % (len(ok), len(ok) + len(miss)))
    for m in miss:
        print("  MISSED:", m)
    return 1 if miss else 0


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    rep = main()
    ch = rep["checks"]
    print("cells:", len(rep["cells"]))
    c4 = ch["C4_uniformity_chi2"]
    print("C4 chi2 (null: chi2_{m-1}): mixer max|z| = %.2f ; plant min|z| = %.2f ; "
          "overall separates = %s" % (
              c4["mixer_max_abs_z"], c4["plant_min_abs_z"], c4["separates_overall"]))
    print("   separation window (alpha where the certificate has power): %s" %
          [round(x, 2) for x in c4["separation_window_alpha"]])
    print("   power by load (plant_min|z|): %s" %
          {k: round(v["plant_min_abs_z"], 1) for k, v in sorted(c4["power_by_load"].items())})
    print("C10 deviation from the LINEAR formula (mean / spread):")
    c10 = ch["C10_deviation_from_linear_formula"]
    for a in (0.50, 0.80, 0.90, 0.95, 0.99):
        print("   a=%.2f  linear %+.3f/%.3f   robinhood %+.3f/%.3f" % (
            a, c10["linear|%.2f" % a]["mean"], c10["linear|%.2f" % a]["spread"],
            c10["robinhood|%.2f" % a]["mean"], c10["robinhood|%.2f" % a]["spread"]))
    print("C8 budget control (alpha* increasing in k_max):")
    for k, v in sorted(ch["C8_budget_control"].items()):
        print("   %-34s monotone=%s resolved=%d/%d" % (
            k, v["monotone_increasing"], v["n_resolved"], v["n_resolved"] + v["n_unbracketed"]))
    for arm in ("linear|uniform|lookup_fail", "linear|uniform|insert_fail"):
        print("C7 alpha*(k_max) at level 1e-3 (%s):" % arm)
        for k, row in sorted(ch["C7_budget_boundary"][arm].items(),
                             key=lambda kv: int(kv[0])):
            a = row["alpha_star"]
            print("   k=%-3s alpha*=%-7s formula-mean=%.3f gap_f=%-7s meas-mean=%-7s gap_m=%s %s" % (
                k, "%.4f" % a if a is not None else "undef",
                row["formula_mean_load"],
                "%.4f" % row["gap_vs_formula"] if row["gap_vs_formula"] is not None else "undef",
                "%.4f" % row["measured_mean_load"] if row["measured_mean_load"] is not None else "undef",
                "%.4f" % row["gap_vs_measured_mean"] if row["gap_vs_measured_mean"] is not None else "undef",
                ("[" + row["bound"] + "-bound]") if row.get("bound") else ""))
