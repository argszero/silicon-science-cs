"""Canonical one-command runner for issue #1.

Single entry point that reproduces every number in the manuscript:

  1. reader-fidelity gate (eval_fidelity.py) writes fidelity_results.json, 12 checks
  2. full corrected sweep (grid6.build_plan over grid6.run_cell) writes grid6_results.json
  3. derivation (analyze6.py) writes grid6_analysis.json
  4. canonical artefact writes canonical_results.json, byte-identical across runs

Determinism contract: no wall-clock field is written anywhere into the canonical artefact.
The runner prints its own wall-clock, but that value is NOT part of any hashed payload
(lesson from issue #93 R241: a per-cell timing field survived one round of cleanup because a
same-machine byte-identical check cannot see a field that is stable on one machine).

Usage: python canonical_runner.py
"""
import hashlib, json, os, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

CANONICAL = os.path.join(HERE, "canonical_results.json")
RESULTS_JSON = os.path.join(HERE, "grid6_results.json")
ANALYSIS_JSON = os.path.join(HERE, "grid6_analysis.json")
FIDELITY_JSON = os.path.join(HERE, "fidelity_results.json")

TIMING_KEYS = ("seconds", "elapsed", "t_start", "t_end", "wall", "runtime", "sim_seconds",
               "duration", "time", "times", "timestamp", "minutes", "hours")


def strip_timings(obj):
    """Recursively drop wall-clock keys so the artefact is byte-identical across runs."""
    if isinstance(obj, dict):
        return {k: strip_timings(v) for k, v in obj.items() if k not in TIMING_KEYS}
    if isinstance(obj, list):
        return [strip_timings(v) for v in obj]
    return obj


def digest(obj):
    blob = json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(blob).hexdigest()


def run_step(title, argv):
    print("== %s ==" % title)
    t0 = time.time()
    proc = subprocess.run(argv, cwd=HERE, capture_output=True, text=True)
    if proc.returncode != 0:
        print(proc.stdout[-3000:])
        print(proc.stderr[-3000:])
        raise SystemExit("step failed: %s" % title)
    tail = [ln for ln in proc.stdout.strip().split("@" + "n") if ln.strip()][-2:]
    for ln in tail:
        print("   " + ln)
    print("   (%.0f s)" % (time.time() - t0))


def run_sweep():
    """Run the full corrected sweep in-process and write the deterministic raw artefact."""
    import torch
    import grid6

    torch.set_num_threads(10)
    model = grid6.reader_port.Llama(os.path.join(grid6.RD, "config.json"),
                                    os.path.join(grid6.RD, "model.safetensors"))
    tok_m, enc_m = grid6.mini_port.load_minilm()
    plan = grid6.build_plan()
    cells = []
    for arm, inst, n_chunks, inter, kind, filler, gf in plan:
        cells.append(grid6.run_cell(model, tok_m, enc_m, arm, inst, n_chunks, inter,
                                    kind, filler, gf))
    res = {"cells": strip_timings(cells), "plan_size": len(plan), "k": grid6.KS,
           "seeds": grid6.SEEDS, "temperature": grid6.TEMP,
           "environment": {"reader": "SmolLM2-135M port (KV-cached)",
                           "retriever": "MiniLM-L6-v2 port + BM25"}}
    open(RESULTS_JSON, "w").write(json.dumps(res, indent=1, sort_keys=True))
    print("   cells %d" % len(cells))
    return res


def main():
    t_start = time.time()
    run_step("reader fidelity gate", [sys.executable, "eval_fidelity.py"])
    print("== full corrected sweep ==")
    t0 = time.time()
    res = run_sweep()
    print("   (%.0f s)" % (time.time() - t0))
    run_step("derivation", [sys.executable, "analyze6.py"])

    fid = json.load(open(FIDELITY_JSON))
    derived = json.load(open(ANALYSIS_JSON))
    canonical = strip_timings({
        "issue": 1,
        "fidelity": {"verdict": fid.get("verdict"), "held_out": fid.get("held_out"),
                     "kv_cache": fid.get("kv_cache"), "power_check": fid.get("power_check"),
                     "tokenizer": fid.get("tokenizer"), "baselines": fid.get("baselines"),
                     "corpus": fid.get("corpus"), "task_sanity": fid.get("task_sanity")},
        "sweep": {"plan_size": res["plan_size"], "k": res["k"], "seeds": res["seeds"],
                  "temperature": res["temperature"], "environment": res["environment"],
                  "cells": res["cells"]},
        "derived": derived,
    })
    canonical["sha256"] = digest({k: v for k, v in canonical.items() if k != "sha256"})
    open(CANONICAL, "w").write(json.dumps(canonical, indent=1, sort_keys=True))
    print("== CANONICAL DONE ==")
    print("   cells %d | sha256 %s" % (len(res["cells"]), canonical["sha256"]))
    print("   wall-clock %.0f s (not part of the hashed payload)" % (time.time() - t_start))


if __name__ == "__main__":
    main()
