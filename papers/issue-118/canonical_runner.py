#!/usr/bin/env python3
"""canonical_runner -- THE canonical artefact of issue #118.

Five instruments, each owning one question, each writing its own results file.
This runner executes them in order, in this directory, and merges their outputs
into the single `canonical_results.json` that every figure and every number in the
manuscript reads. Determinism is the instruments' own (seed 20261002 fixed in each);
the runner adds no state, no clock and no ordering dependence of its own.

Run: /usr/bin/python3 canonical_runner.py     ->  canonical_results.json
"""
import json
import os
import subprocess
import sys

SEED = 20261002
STEPS = [
    ("spike_v0",      "spike_v0.py",      "spike_v0_results.json",
     "exact tail-sum vs an independent Monte-Carlo; the C_min decomposition"),
    ("spike_v1",      "spike_v1.py",      "spike_v1_results.json",
     "the certified two-route comparison; the tolerance-indexed curve; the ceiling"),
    ("model_v2",      "model_v2.py",      "model_v2_results.json",
     "the closed form and its domain; top-k exactness; the dispatch composition arm"),
    ("probe_uniform", "probe_uniform.py", "probe_uniform_results.json",
     "the uniform router at both ends: the tolerance C = 1.25 encodes, and the floor"),
    ("model_v3",      "model_v3.py",      "model_v3_results.json",
     "the production map; a measured router"),
]


def main():
    merged = {"issue": 118, "seed": SEED, "steps": {}}
    for key, script, out, what in STEPS:
        print("  running %-14s (%s)" % (key, what))
        r = subprocess.run([sys.executable, script], capture_output=True, text=True)
        if r.returncode != 0:
            sys.stderr.write(r.stdout[-3000:] + "\n" + r.stderr[-3000:])
            raise SystemExit("instrument %s FAILED (exit %d)" % (script, r.returncode))
        with open(out) as fh:
            merged["steps"][key] = json.load(fh)
        merged["steps"][key]["_script"] = script
        print("     -> %-26s %7d B" % (out, os.path.getsize(out)))
    with open("canonical_results.json", "w") as fh:
        json.dump(merged, fh, indent=1, sort_keys=True)
    print("\nwrote canonical_results.json  (%d B)" % os.path.getsize("canonical_results.json"))
    headline(merged)


def headline(m):
    v0 = m["steps"]["spike_v0"]
    v1 = m["steps"]["spike_v1"]
    v2 = m["steps"]["model_v2"]
    pr = m["steps"]["probe_uniform"]
    v3 = m["steps"]["model_v3"]
    print("\nHEADLINE (every value below is read from the merged artefact)")
    print("  (i)  two exact routes agree to %.2e   (bar 1e-3)" % v1["worst_rel_AB"])
    print("  (i)  Monte-Carlo scored, max |z| = %.2f over %d cells" % (v1["max_z"], len(v1["cells"])))
    print("  (iv) %d of the mu<=16 cells need C > 1.25 with a PERFECTLY UNIFORM router"
          % v0["ceiling_cells_above_1_25"])
    print("  P1   D(C=1.25) = %.6f at mu=1  /  %.6g at mu=128" % (pr["cells"][0]["drop_at_folk"],
                                                                  pr["cells"][-1]["drop_at_folk"]))
    print("  (ii) closed form (Edgeworth) within the 5%% bar on mu>=8: max %.4f"
          % v2["ii_edge_domain_max_rel"])
    print("  P3   first-decile share %.4f, last-decile share %.4f"
          % (v2["p3"][0]["first_decile_share"], v2["p3"][0]["last_decile_share"]))
    print("  (v)  %d production configurations placed on the curve" % len(v3["arm1_configs"]))
    ar = v3["arm2_measured_router"]
    floor = pr["floor"]["c_min"]
    cms = [r["c_min"] for r in ar["sweep"]]
    print("  (vi) measured router: C_min %.2f (no balancing) -> %.2f at the heaviest weight,"
          % (cms[0], cms[-1]))
    print("       minimum %.2f; uniform C_min floor %.4f" % (min(cms), floor))
    print("       (the max/mean RATIO floor at the same cell is %.4f by the max-order form,"
          % ar["uniform_floor_theory"])
    print("        %.4f +- %.4f by 500-draw Monte-Carlo -- a different quantity, on a different axis)"
          % (ar["uniform_floor_mc"], ar["uniform_floor_sd"]))


if __name__ == "__main__":
    main()
