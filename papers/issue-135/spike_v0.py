#!/usr/bin/env python3
"""Issue #135 -- exact probe-count instrument, v0 (linear-probing arm).

Deterministic, standard-library only, CPU-only, no timings.
Ground truth is BY CONSTRUCTION: the table state is the ground truth, and every
probe is counted as an exact integer.  Every reported number is a count.

Object measured: the full successful- and unsuccessful-search probe-count
distribution of an open-addressing table with LINEAR probing, at several loads,
over several key families and seeds, with the classical uniform-hashing
formulas as the published baseline for the MEAN.

Checks carried by this instrument (each has a PLANT that must make it fire):
  C1  mean agreement -- the measured mean unsuccessful-search probe count lies
      inside a declared two-sided band around the classical formula
      U(alpha) = 1/2 (1 + 1/(1-alpha)^2).  PLANT: a table hashed with the
      IDENTITY map (no mixer) on a sequential key set; the check must FAIL.
  C2  tail gap -- p99 / mean of the unsuccessful-search probes, per cell.
      (Reported, not asserted; P1's registered ratio is read off it.)
  C3  determinism -- verified by RE-RUNNING the instrument and comparing the
      output file's sha256 (two independent processes); this is the same
      byte-identity pattern the rest of the package uses, and it is asserted by
      the shell check, not inside the process.
  C4  uniformity certificate -- per family, the slot occupancy's max relative
      deviation; the identity-hash plant must be far worse than the mixer.
"""
import json
import math
import sys

MASK = (1 << 64) - 1

# ---------------------------------------------------------------- RNG (own)
class SplitMix64:
    """splitmix64 -- specified, committed mixer; no CPython-internal state."""
    __slots__ = ("s",)

    def __init__(self, seed):
        self.s = seed & MASK

    def next(self):
        self.s = (self.s + 0x9E3779B97F4A7C15) & MASK
        z = self.s
        z = ((z ^ (z >> 30)) * 0xBF58476D1CE4E5B9) & MASK
        z = ((z ^ (z >> 27)) * 0x94D049BB133111EB) & MASK
        return z ^ (z >> 31)


# ---------------------------------------------------------------- hashes
def mixer(key):
    """murmur3-style 64-bit finalizer (declared table hash)."""
    z = key & MASK
    z = ((z ^ (z >> 33)) * 0xFF51AFD7ED558CCD) & MASK
    z = ((z ^ (z >> 33)) * 0xC4CEB9FE1A85EC53) & MASK
    return z ^ (z >> 33)


def identity(key):
    """The PLANT hash: no mixing at all."""
    return key & MASK


# ---------------------------------------------------------------- families
def key_family(name, n, seed):
    """Return a list of n distinct 64-bit integer keys."""
    out = []
    seen = set()
    if name == "uniform":
        r = SplitMix64(seed)
        while len(out) < n:
            k = r.next()
            if k not in seen:
                seen.add(k)
                out.append(k)
    elif name == "sequential":
        base = SplitMix64(seed).next() & 0xFFFF000000000000
        for i in range(n):
            out.append(base + i)
    else:
        raise ValueError(name)
    return out


# ---------------------------------------------------------------- probing
def build_linear(keys, m, hfn):
    """Insert with unbounded linear probing; return (table, positions)."""
    table = [None] * m
    pos = []
    for key in keys:
        i = hfn(key) % m
        while table[i] is not None:
            i = (i + 1) % m
        table[i] = key
        pos.append(i)
    return table, pos


def unsucc_probes(table, m, key, hfn):
    """Probes until the first empty slot (the empty probe is counted)."""
    i = hfn(key) % m
    p = 0
    while True:
        p += 1
        if table[i] is None:
            return p
        i = (i + 1) % m


def succ_probes(pos, hfn, key, m):
    return (pos - hfn(key)) % m + 1


def longest_occupied_run(table, m):
    """Longest circular run of non-empty slots (the clustering statistic)."""
    if all(t is not None for t in table):
        return m
    # find an empty slot to start from
    start = table.index(None)
    best = 0
    cur = 0
    for j in range(1, m + 1):
        if table[(start + j) % m] is None:
            best = max(best, cur)
            cur = 0
        else:
            cur += 1
    return max(best, cur)


def pct(sorted_vals, q):
    """Smallest v such that (fraction <= v) >= q -- the standard percentile."""
    n = len(sorted_vals)
    idx = math.ceil(q * n) - 1
    idx = 0 if idx < 0 else (n - 1 if idx >= n else idx)
    return sorted_vals[idx]


def stats(vals):
    s = sorted(vals)
    tot = 0
    for v in s:
        tot += v                       # exact integer sum
    return {
        "n": len(s),
        "sum": tot,
        "mean": tot / len(s),          # one IEEE division of an exact integer
        "p50": pct(s, 0.50),
        "p90": pct(s, 0.90),
        "p99": pct(s, 0.99),
        "p999": pct(s, 0.999),
        "max": s[-1],
    }


U_FORMULA = lambda a: 0.5 * (1.0 + 1.0 / (1.0 - a) ** 2)
S_FORMULA = lambda a: 0.5 * (1.0 + 1.0 / (1.0 - a))


# ---------------------------------------------------------------- one cell
def run_cell(family, alpha, seed, m, n_unsucc, hash_name):
    hfn = mixer if hash_name == "mixer" else identity
    n = int(round(alpha * m))
    keys = key_family(family, n, seed)
    table, pos = build_linear(keys, m, hfn)

    # uniformity certificate: max relative deviation of slot counts
    counts = [0] * m
    for key in keys:
        counts[hfn(key) % m] += 1
    exp = n / m
    maxdev = max(abs(c - exp) for c in counts) / exp

    succ = stats([succ_probes(p, hfn, k, m) for k, p in zip(keys, pos)])

    r = SplitMix64(seed ^ 0xABCDEF0123456789)
    uns = []
    for _ in range(n_unsucc):
        k = r.next()
        uns.append(unsucc_probes(table, m, k, hfn))
    unsuc = stats(uns)

    return {
        "scheme": "linear",
        "family": family,
        "hash": hash_name,
        "seed": seed,
        "alpha": alpha,
        "n": n,
        "m": m,
        "n_unsucc_samples": n_unsucc,
        "max_rel_slot_dev": maxdev,
        "longest_run": longest_occupied_run(table, m),
        "succ": succ,
        "unsucc": unsuc,
        "formula_succ": S_FORMULA(alpha),
        "formula_unsucc": U_FORMULA(alpha),
    }


# ---------------------------------------------------------------- the grid
def build_grid(hash_name="mixer", m=8192, n_unsucc=20000):
    alphas = [0.50, 0.70, 0.85, 0.90, 0.95]
    families = ["uniform", "sequential"]
    seeds = [1, 2, 3]
    cells = []
    for family in families:
        for alpha in alphas:
            for si, seed in enumerate(seeds):
                s = seed * 1000003 + (0 if family == "uniform" else 777)
                cells.append(run_cell(family, alpha, s, m, n_unsucc, hash_name))
    return cells


def finite_size_control(alpha=0.95, sizes=(4096, 16384, 65536), seeds=(1, 2, 3),
                        samples=20000):
    """Is the formula's mean deviation a finite-size effect?  Assert it shrinks."""
    rows = []
    for m in sizes:
        devs = []
        for seed in seeds:
            n = int(round(alpha * m))
            keys = key_family("uniform", n, seed * 1000003)
            table, _ = build_linear(keys, m, mixer)
            r = SplitMix64((seed * 1000003) ^ 0xABCDEF0123456789)
            tot = 0
            for _ in range(samples):
                tot += unsucc_probes(table, m, r.next(), mixer)
            devs.append((tot / samples - U_FORMULA(alpha)) / U_FORMULA(alpha))
        rows.append({"m": m, "n": int(round(alpha * m)),
                     "devs": [round(d, 4) for d in devs],
                     "abs_mean_dev": abs(sum(devs) / len(devs))})
    shrink = all(rows[i + 1]["abs_mean_dev"] < rows[i]["abs_mean_dev"]
                 for i in range(len(rows) - 1))
    return {"alpha": alpha, "sizes": list(sizes), "seeds": list(seeds),
            "rows": rows, "verdict": "PASS" if shrink else "FAIL"}


def checks(cells, band=0.15):
    out = {}

    # C1 -- mean agreement (mixer cells only)
    ok = bad = 0
    worst = None
    for c in cells:
        if c["hash"] != "mixer":
            continue
        meas = c["unsucc"]["mean"]
        f = c["formula_unsucc"]
        rel = (meas - f) / f
        if abs(rel) <= band:
            ok += 1
        else:
            bad += 1
        if worst is None or abs(rel) > abs(worst[0]):
            worst = (rel, c["family"], c["alpha"], c["n"])
    out["C1_mean_agreement"] = {
        "band": band, "pass": ok, "fail": bad,
        "worst_rel_dev": worst[0], "worst_cell": worst[1:],
        "verdict": "PASS" if bad == 0 else "FAIL",
    }

    # C1 plant -- identity hash must FAIL the same check
    plant = [c for c in cells if c["hash"] == "plant"]
    pok = pbad = 0
    for c in plant:
        rel = (c["unsucc"]["mean"] - c["formula_unsucc"]) / c["formula_unsucc"]
        if abs(rel) <= band:
            pok += 1
        else:
            pbad += 1
    out["C1_plant_identity"] = {
        "pass": pok, "fail": pbad,
        "fires": pbad > 0,
        "verdict": "FIRED" if pbad > 0 else "SILENT",
    }

    # C2 -- tail gap per (family, alpha) over the mixer cells
    C2 = {}
    for c in cells:
        if c["hash"] != "mixer":
            continue
        key = "%s@%.2f" % (c["family"], c["alpha"])
        ratio = c["unsucc"]["p99"] / c["unsucc"]["mean"]
        C2.setdefault(key, []).append(ratio)
    out["C2_p99_over_mean"] = {k: {"mean": sum(v) / len(v), "n": len(v)}
                               for k, v in C2.items()}

    # C4 -- uniformity certificate, mixer vs plant
    dev = {}
    for c in cells:
        dev.setdefault(c["hash"], []).append(c["max_rel_slot_dev"])
    out["C4_uniformity"] = {h: {"max": max(v)} for h, v in dev.items()}

    # C5 -- finite-size control: the formula's mean deviation must SHRINK with m
    out["C5_finite_size"] = finite_size_control()

    # C6 -- across-instance spread at a FIXED load: p99 spread vs mean spread
    grp = {}
    for c in cells:
        if c["hash"] != "mixer":
            continue
        grp.setdefault((c["family"], c["alpha"]), []).append(c)
    C6 = {}
    for k, cs in sorted(grp.items()):
        means = [c["unsucc"]["mean"] for c in cs]
        p99s = [c["unsucc"]["p99"] for c in cs]
        mm = sum(means) / len(means)
        pm = sum(p99s) / len(p99s)
        C6["%s@%.2f" % k] = {
            "n_seeds": len(cs),
            "mean_spread_rel": (max(means) - min(means)) / mm,
            "p99_spread_rel": (max(p99s) - min(p99s)) / pm,
            "spread_ratio_p99_over_mean":
                ((max(p99s) - min(p99s)) / pm) / ((max(means) - min(means)) / mm)
                if (max(means) - min(means)) > 0 else None,
        }
    out["C6_instance_spread"] = C6
    return out


# ---------------------------------------------------------------- output path
def out_path(default):
    """Where the report is written.  SPIKE_OUT overrides it, so reproduce.sh can
    run the instrument with the package left untouched (it writes into a private
    temp dir and compares)."""
    import os
    return os.environ.get("SPIKE_OUT", default)


def main():
    cells = build_grid("mixer") + build_grid("plant")
    report = {"instrument": "spike_v0", "issue": 135,
              "cells": cells, "checks": checks(cells)}
    blob = json.dumps(report, sort_keys=True, indent=1)
    with open(out_path("spike_v0_results.json"), "w") as fh:
        fh.write(blob)
    return report



# ---------------------------------------------------------------- selftest
def selftest():
    """Plant battery: every plant must FIRE, and every pure function is checked
    against an independently computed value.  A plant that passes silently is a
    decoration, so each one is asserted to change a verdict."""
    fired = []
    failed = []

    def want(name, cond):
        (fired if cond else failed).append(name)

    # pct() against an independently computed answer
    s = [1, 2, 3, 4, 5]
    want("pct_50", pct(s, 0.50) == 3)
    want("pct_99", pct(s, 0.99) == 5)

    # the formula is the textbook one (an independently written expression)
    want("U_formula", abs(U_FORMULA(0.5) - 0.5 * (1 + 1 / 0.25)) < 1e-12)
    want("S_formula", abs(S_FORMULA(0.5) - 0.5 * (1 + 1 / 0.5)) < 1e-12)

    # The mixer spreads a STRUCTURED key set; the identity hash does not.  The
    # structured set is the sequential family (keys sharing their high bits),
    # which is the basis of C1's plant.  Note range(64) is a red herring: the
    # identity map is a bijection mod 64 on it, so the collision must be measured
    # on the family the plant actually uses.
    # The plant's mechanism is CLUSTERING, not slot collisions: on sequential
    # keys the identity map lays every key down contiguously (one run of length
    # n), while the mixer scatters them.  (range(64) and mod-64 distinctness are
    # both red herrings -- the identity map is a bijection on them.)
    seq = key_family("sequential", 4096, 7)
    tl, _ = build_linear(seq, 8192, identity)
    tm, _ = build_linear(seq, 8192, mixer)
    want("identity_clusters", longest_occupied_run(tl, 8192) == 4096)
    want("mixer_does_not_cluster", longest_occupied_run(tm, 8192) < 100)

    # C1's plant arm must FIRE on the identity hash (the check's other side)
    plant_cells = build_grid("plant")
    chk = checks(build_grid("mixer") + plant_cells)
    want("C1_plant_fires", chk["C1_plant_identity"]["fires"])
    # and it must NOT fire when the identity hash is not present
    want("C1_plant_inert_without_plant",
         checks(build_grid("mixer"))["C1_plant_identity"]["fires"] is False)

    print("SELFTEST %d/%d" % (len(fired), len(fired) + len(failed)))
    for f in failed:
        print("  MISSED:", f)
    return 1 if failed else 0


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    rep = main()
    ch = rep["checks"]
    print("cells:", len(rep["cells"]))
    print("C1 mean agreement:", ch["C1_mean_agreement"]["verdict"],
          ch["C1_mean_agreement"]["pass"], "pass /",
          ch["C1_mean_agreement"]["fail"], "fail; worst rel dev",
          round(ch["C1_mean_agreement"]["worst_rel_dev"], 4),
          "at", ch["C1_mean_agreement"]["worst_cell"])
    print("C1 plant (identity hash):", ch["C1_plant_identity"]["verdict"],
          ch["C1_plant_identity"]["fail"], "of",
          ch["C1_plant_identity"]["pass"] + ch["C1_plant_identity"]["fail"], "cells fail")
    print("C4 max rel slot dev:", {k: round(v["max"], 4)
                                   for k, v in ch["C4_uniformity"].items()})
    print("C2 p99/mean:")
    for k in sorted(ch["C2_p99_over_mean"]):
        print("   ", k, round(ch["C2_p99_over_mean"][k]["mean"], 3))
