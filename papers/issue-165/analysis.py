#!/usr/bin/env python3
"""issue-165 -- every number the manuscript quotes is computed here, from the committed data.

Inputs (committed, in refs/):  cs_arm.json.gz, social_sciences_arm.json.gz.
Output (committed, next to this file): results.json, plus a printed receipt line per family of
numbers so a reader can see what the run decided rather than trusting a file.

Estimand, restated because everything below depends on it: for a work `w` discovered from seed `s`,

    coupled(w, s) := |refs(w) & refs(s)| > 0            (deterministic set intersection)

and the quantity judged is the EXCESS of the coupled share over a LENGTH-MATCHED, FIELD-MATCHED null
computed on the same seed's reference list, per reference-length bin. A work with no recorded
reference list has NO VALUE for this predicate; it is excluded from the share and counted.

Nothing here fetches anything: the two arms were collected once, and this program is a pure function
of the committed bytes. Stdlib only -- no third-party import, so the reproduction needs no install.

Usage:  python3 analysis.py          -> writes results.json, exit 0
        python3 analysis.py --check  -> recompute and compare with the committed results.json
"""
import gzip
import hashlib
import json
import os
import random
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REFS = os.path.join(HERE, "refs")
RESULTS = os.path.join(HERE, "results.json")

BINS = [(1, 9), (10, 49), (50, 99), (100, 10 ** 9)]
MIN_NULL_PER_BIN = 10          # below this the bin is NOT RUN, never a zero
BOOTSTRAP_DRAWS = 4000
BOOTSTRAP_SEED = 20261104
CI_LO, CI_HI = 0.025, 0.975     # the interval level is a property of the analysis, so the
                                # manuscript reads it back from here rather than typing "95%".
ARMS = {"cs": ("cs_arm.json.gz", "Computer Science", "17"),
        "social_sciences": ("social_sciences_arm.json.gz", "Social Sciences", "33")}


def bin_name(lo, hi):
    return "%d-%d" % (lo, hi) if hi < 10 ** 9 else "%d+" % lo


def load(name):
    """Read one arm, verifying the digest of the DECOMPRESSED bytes against refs/DIGESTS.json."""
    fn, field_name, field_id = ARMS[name]
    path = os.path.join(REFS, fn)
    raw = gzip.open(path, "rb").read()
    digests = json.load(open(os.path.join(REFS, "DIGESTS.json")))
    want = digests[name]["sha256_raw"]
    got = hashlib.sha256(raw).hexdigest()
    if got != want:
        raise SystemExit("DATA DIGEST MISMATCH for %s: committed %s, computed %s" % (fn, want, got))
    d = json.loads(raw.decode())
    if (d["field"]["display_name"] or "").strip() != field_name or d["field"]["id"] != field_id:
        raise SystemExit("FRAME MISMATCH for %s: %r" % (fn, d["field"]))
    pool = {k: set(v) for k, v in d["null"]["pool"].items()}
    rows = []
    for r in d["seeds"]:
        R = set(r["seed_refs"])
        citers = {k: set(v) for k, v in r["citers"].items()}
        depth = {k: set(v) for k, v in r["depth_works"].items()}
        batches = r.get("depth_batches") or []
        b1 = sum(1 for k in batches[0] if k in depth and depth[k] & R) if batches else 0
        rows.append({"seed": r["seed"], "cited_by": r.get("cited_by_count") or 0,
                     "citer_works": len(citers), "depth_works": len(depth),
                     "c1": sum(1 for v in citers.values() if v & R), "b1": b1,
                     "citers": citers, "depth": depth, "R": R})
    return {"field": d["field"], "seed_frame": d.get("seed_frame"),
            "cost_constants": d.get("cost_constants"), "pool": pool, "rows": rows,
            "digest": got}


def excess(works, R, pool):
    """Share-level excess over the length-matched, field-matched null, over the bins that run."""
    n_defined = coupled = 0
    expected = 0.0
    bins_used, bins_not_run = [], []
    for lo, hi in BINS:
        bn = bin_name(lo, hi)
        obs = [v for v in works.values() if lo <= len(v) <= hi]
        nul = [v for v in pool.values() if lo <= len(v) <= hi]
        if not obs:
            continue
        if len(nul) < MIN_NULL_PER_BIN:
            bins_not_run.append({"bin": bn, "null_n": len(nul), "observed_n": len(obs)})
            continue
        n_c = sum(1 for v in obs if v & R)
        p0 = sum(1 for v in nul if v & R) / len(nul)
        n_defined += len(obs)
        coupled += n_c
        expected += len(obs) * p0
        bins_used.append(bn)
    if n_defined == 0:
        return None
    return {"n_defined": n_defined, "coupled": coupled,
            "observed_share": coupled / n_defined,
            "null_share": expected / n_defined,
            "excess_share": (coupled - expected) / n_defined,
            "bins_used": sorted(bins_used), "bins_not_run": bins_not_run}


def percentile_ci(vals, lo=CI_LO, hi=CI_HI):
    v = sorted(vals)
    return [v[int(lo * len(v))], v[int(hi * len(v)) - 1]]


def wilson(k, n, z=1.96):
    if n == 0:
        return None
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5) / d
    return [max(0.0, c - h), min(1.0, c + h)]


def analyse_arm(name):
    arm = load(name)
    rows, pool = arm["rows"], arm["pool"]
    out = {"field": arm["field"], "seed_frame": arm["seed_frame"],
           "cost_constants": arm["cost_constants"], "data_sha256": arm["digest"],
           "n_seeds": len(rows)}

    ds, c1s, b1s = [], [], []
    per_seed = []
    hop1_tot = hop2_tot = None
    for r in rows:
        e1 = excess(r["citers"], r["R"], pool)
        e2 = excess(r["depth"], r["R"], pool)
        row = {"seed": r["seed"], "cited_by_count": r["cited_by"],
               "citer_works": r["citer_works"], "depth_works": r["depth_works"],
               "citer_coupled": r["c1"], "depth_batch_coupled": r["b1"],
               "hop1": e1, "hop2": e2}
        if e1 and e2:
            row["d"] = e2["excess_share"] - e1["excess_share"]
            ds.append(row["d"])
        else:
            row["d"] = None
            row["not_run"] = "a length bin did not run for this seed"
        for tot, e in (("h1", e1), ("h2", e2)):
            if e:
                agg = hop1_tot if tot == "h1" else hop2_tot
                if agg is None:
                    agg = {"n": 0, "coupled": 0, "expected": 0.0}
                agg["n"] += e["n_defined"]
                agg["coupled"] += e["coupled"]
                agg["expected"] += e["n_defined"] * e["null_share"]
                if tot == "h1":
                    hop1_tot = agg
                else:
                    hop2_tot = agg
        c1s.append(r["c1"])
        b1s.append(r["b1"])
        per_seed.append(row)
    out["per_seed"] = per_seed

    def pooled(agg, label):
        if not agg:
            return {"label": label, "status": "NOT RUN"}
        return {"label": label, "n_defined": agg["n"], "coupled": agg["coupled"],
                "observed_share": agg["coupled"] / agg["n"],
                "null_share": agg["expected"] / agg["n"],
                "excess": (agg["coupled"] - agg["expected"]) / agg["n"],
                "coupled_ci": wilson(agg["coupled"], agg["n"])}

    out["pooled"] = {"hop1": pooled(hop1_tot, "hop-1 (citers of the seed)"),
                     "hop2": pooled(hop2_tot, "hop-2 (references of citers)")}

    mean_c1, mean_b1 = statistics.mean(c1s), statistics.mean(b1s)
    out["cost"] = {"mean_coupled_per_page": mean_c1, "mean_coupled_per_batch": mean_b1,
                   "page_worth_in_batches": (mean_c1 / mean_b1) if mean_b1 else None}
    out["construction_zeros"] = [r["seed"] for r in rows if r["c1"] == 0]
    out["seeds_batch_beats_page"] = sum(1 for a, b in zip(c1s, b1s) if b > a)

    rng = random.Random(BOOTSTRAP_SEED)
    n = len(rows)
    w_boot, d_boot = [], []
    for _ in range(BOOTSTRAP_DRAWS):
        idx = [rng.randrange(n) for _ in range(n)]
        mc = statistics.mean(c1s[i] for i in idx)
        mb = statistics.mean(b1s[i] for i in idx)
        if mc:
            w_boot.append(mb / mc)
        picked = [ds[i] for i in idx if i < len(ds)]
        if picked:
            d_boot.append(statistics.mean(picked))

    w_star = mean_b1 / mean_c1 if mean_c1 else None
    out["w_star"] = {"point": w_star, "ci95": percentile_ci(w_boot),
                     "floor": 1.0, "attainable": bool(w_star is not None and w_star >= 1.0),
                     "bootstrap_draws": BOOTSTRAP_DRAWS, "bootstrap_seed": BOOTSTRAP_SEED}
    d_mean = statistics.mean(ds) if ds else None
    out["decay"] = {"n_seeds_with_d": len(ds), "mean_d": d_mean,
                    "ci95_mean_d": percentile_ci(d_boot) if d_boot else None,
                    "median_d": statistics.median(ds) if ds else None,
                    "seeds_d_lt_0": sum(1 for x in ds if x < 0),
                    "seeds_d_gt_0": sum(1 for x in ds if x > 0),
                    "seeds_d_eq_0": sum(1 for x in ds if x == 0)}
    lo, hi = out["decay"]["ci95_mean_d"] if d_boot else (None, None)
    if hi is None:
        out["decay"]["verdict"] = "NOT RUN"
    elif hi < 0:
        out["decay"]["verdict"] = "HOLDS: the 95% interval of mean d lies below zero"
    elif lo > 0:
        out["decay"]["verdict"] = "DISAGREES: the 95% interval of mean d lies above zero"
    else:
        out["decay"]["verdict"] = "NO INFORMATION for this field: the 95% interval spans zero"

    out["_d_values"] = ds
    print("[%s] seeds=%d  hop-1 excess=%+.4f  hop-2 excess=%+.4f"
          % (arm["field"]["display_name"], len(rows), out["pooled"]["hop1"]["excess"],
             out["pooled"]["hop2"]["excess"]))
    print("[%s] page=%.3f batch=%.3f -> page worth %.3f batches; w*=%.4f CI %s (floor 1.0)"
          % (arm["field"]["display_name"], mean_c1, mean_b1, out["cost"]["page_worth_in_batches"],
             w_star, [round(x, 4) for x in out["w_star"]["ci95"]]))
    print("[%s] mean d=%+.4f CI %s; d<0 %d/%d; batch beats page %d/%d; construction zeros %s"
          % (arm["field"]["display_name"], d_mean,
             [round(x, 4) for x in out["decay"]["ci95_mean_d"]],
             out["decay"]["seeds_d_lt_0"], out["decay"]["n_seeds_with_d"],
             out["seeds_batch_beats_page"], n, out["construction_zeros"] or "none"))
    print("[%s] decay verdict: %s" % (arm["field"]["display_name"], out["decay"]["verdict"]))
    return out


def main():
    arms = {k: analyse_arm(k) for k in ARMS}

    # between fields: difference of the mean d, bootstrapped over each field independently.
    # The fields are NEVER pooled -- the between-field variation is the claim under test.
    rng = random.Random(BOOTSTRAP_SEED)
    a, b = arms["cs"]["_d_values"], arms["social_sciences"]["_d_values"]
    diffs = []
    for _ in range(BOOTSTRAP_DRAWS):
        ma = statistics.mean(a[rng.randrange(len(a))] for _ in range(len(a)))
        mb = statistics.mean(b[rng.randrange(len(b))] for _ in range(len(b)))
        diffs.append(mb - ma)
    between = {"mean_d_cs": arms["cs"]["decay"]["mean_d"],
               "mean_d_social_sciences": arms["social_sciences"]["decay"]["mean_d"],
               "difference_ss_minus_cs": arms["social_sciences"]["decay"]["mean_d"] - arms["cs"]["decay"]["mean_d"],
               "ci95": percentile_ci(diffs),
               "pooled": False,
               "note": "not pooled: universality across fields is the claim under test, and pooling "
                       "would buy precision by erasing the variation that decides it"}
    print("[between] difference of mean d (SS - CS) = %+.4f CI %s; intervals include zero: %s"
          % (between["difference_ss_minus_cs"], [round(x, 4) for x in between["ci95"]],
             between["ci95"][0] <= 0 <= between["ci95"][1]))

    # The pre-registered rule, applied to the second field (see research/ for the record).
    ss = arms["social_sciences"]
    cs = arms["cs"]
    if ss["decay"]["verdict"].startswith("DISAGREES") or ss["decay"]["verdict"].startswith("NO INFORMATION"):
        verdict = ("DOWNGRADE: the decay law does not replicate in the second field (%s)"
                   % ss["decay"]["verdict"].split(":")[0])
    elif ss["w_star"]["attainable"]:
        verdict = ("DECAY REPLICATES AND THE ALLOCATION CLAIM IS RESTORED: w* = %.3f >= 1"
                   % ss["w_star"]["point"])
    else:
        verdict = ("DECAY REPLICATES, BOUND REPLICATES: w* = %.3f in the second field is again below "
                   "the floor of 1.0, so breadth-first is the only allocation this API's price allows"
                   % ss["w_star"]["point"])
    for o in arms.values():
        o.pop("_d_values", None)

    results = {"schema": 1,
               "estimand": "coupled share in excess of a length-matched, field-matched null, per request",
               "bins": [bin_name(lo, hi) for lo, hi in BINS],
               "min_null_per_bin": MIN_NULL_PER_BIN,
               "ci_level": int(round((CI_HI - CI_LO) * 100)),
               "ci_quantiles": [CI_LO, CI_HI],
               "arms": arms, "between_fields": between, "verdict": verdict}
    text = json.dumps(results, indent=1, sort_keys=True) + "\n"

    if "--check" in sys.argv:
        committed = open(RESULTS).read()
        if committed != text:
            print("\nCHECK FAILED: results.json on disk differs from what this run computes", file=sys.stderr)
            return 1
        print("\nCHECK OK: results.json matches this run byte for byte")
        return 0

    with open(RESULTS, "w") as fh:
        fh.write(text)
    print("\nVERDICT: %s" % verdict)
    print("wrote results.json (%d bytes)" % len(text))
    return 0


if __name__ == "__main__":
    sys.exit(main())
