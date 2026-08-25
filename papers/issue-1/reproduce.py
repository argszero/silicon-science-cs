"""
reproduce.py — one-command reproduction of all manuscript experiments.

Usage: python3 reproduce.py [--output DIR]

Runs Experiments 1–4 (density sweep, chains, requeue recovery, deadlock
prediction) with the manuscript's exact seeds and prints the headline tables.
With --output DIR, writes machine-readable results to DIR/results.json and
per-experiment text dumps.

Expected output (deterministic; seeds fixed): see expected_output/.
"""
from __future__ import annotations

import argparse
import json
import os
import random
import sys
import time

from sim import Cluster, least_requested_score, best_fit_score, schedule, schedule_with_requeue
from gen import gen_cluster, gen_pods, gen_chain_pods
from opt import optimal_placement
from detect import predict_deadlocks, root_scc_sizes


def exp1():
    """Density sweep (n=20 seeds/density). Returns summary rows."""
    rows = []
    for d in [0.0, 0.25, 0.5, 0.75, 1.0]:
        gaps, gs, bs, rs, os_, pos = [], [], [], [], [], 0
        for s in range(20):
            rng = random.Random(s)
            pods = gen_pods(rng, n_types=3, per_type=2, density=d)
            cluster = Cluster(nodes=gen_cluster(rng))
            order = list(range(len(pods)))
            rng.shuffle(order)
            g = schedule(cluster, pods, order, least_requested_score)
            b = schedule(cluster, pods, order, best_fit_score)
            r = schedule(cluster, pods, order, None, rng=random.Random(s + 1))
            o = optimal_placement(cluster, pods)
            gp = g["n_placed"] / len(pods)
            gaps.append((o["n_placed"] - g["n_placed"]) / max(1, o["n_placed"]))
            gs.append(gp); bs.append(b["n_placed"] / len(pods))
            rs.append(r["n_placed"] / len(pods)); os_.append(o["n_placed"] / len(pods))
            if gaps[-1] > 0:
                pos += 1
        rows.append({"density": d, "mean_gap": sum(gaps) / len(gaps),
                     "greedy": sum(gs) / len(gs), "bestfit": sum(bs) / len(bs),
                     "random": sum(rs) / len(rs), "optimal": sum(os_) / len(os_),
                     "gap_gt0": pos})
    return rows


def exp2():
    """Requeue recovery (n=10 seeds): chains + mutual-affinity density=1.0."""
    rows = []
    configs = [
        ("2ch L=2", lambda rng: gen_chain_pods(rng, n_chains=2, chain_len=2, per_type=1),
         lambda rng: gen_cluster(rng, n_racks=2, nodes_per_rack=2)),
        ("2ch L=3", lambda rng: gen_chain_pods(rng, n_chains=2, chain_len=3, per_type=1),
         lambda rng: gen_cluster(rng, n_racks=2, nodes_per_rack=2)),
        ("2ch L=4", lambda rng: gen_chain_pods(rng, n_chains=2, chain_len=4, per_type=1),
         lambda rng: gen_cluster(rng, n_racks=2, nodes_per_rack=2)),
        ("2ch L=3 anti25", lambda rng: gen_chain_pods(rng, n_chains=2, chain_len=3, per_type=1, anti_fraction=0.25),
         lambda rng: gen_cluster(rng, n_racks=2, nodes_per_rack=2)),
        ("density=1.0 (mutual)", lambda rng: gen_pods(rng, n_types=3, per_type=2, density=1.0),
         lambda rng: gen_cluster(rng)),
    ]
    for name, gen_p, gen_c in configs:
        sps, rqs, opts, ratios, rounds = [], [], [], [], 0
        unrec = 0
        for s in range(10):
            rng = random.Random(s)
            pods = gen_p(rng)
            cluster = Cluster(nodes=gen_c(rng))
            order = list(range(len(pods)))
            rng.shuffle(order)
            sp = schedule(cluster, pods, order, least_requested_score)
            rq = schedule_with_requeue(cluster, pods, order, least_requested_score,
                                       rng=random.Random(s + 2), max_retries=200)
            opt = optimal_placement(cluster, pods)
            sps.append(sp["n_placed"] / len(pods))
            rqs.append(rq["n_placed"] / len(pods))
            opts.append(opt["n_placed"] / len(pods))
            ratios.append(rq["checks"] / max(1, sp["checks"]))
            rounds = max(rounds, rq["rounds"])
            unrec += len(rq["unplaced"])
        n = len(sps)
        rows.append({"config": name,
                     "single_pass": sum(sps) / n, "requeue": sum(rqs) / n,
                     "optimal": sum(opts) / n, "check_ratio": sum(ratios) / n,
                     "max_rounds": rounds, "unrecoverable": unrec})
    return rows


def exp3():
    """Deadlock prediction (n=10 seeds). Returns rows."""
    rows = []
    regimes = [
        ("density=1.0", lambda rng: gen_pods(rng, n_types=3, per_type=2, density=1.0),
         lambda rng: gen_cluster(rng)),
        ("density=0.75", lambda rng: gen_pods(rng, n_types=3, per_type=2, density=0.75),
         lambda rng: gen_cluster(rng)),
        ("density=0.5", lambda rng: gen_pods(rng, n_types=3, per_type=2, density=0.5),
         lambda rng: gen_cluster(rng)),
        ("density=0.25", lambda rng: gen_pods(rng, n_types=3, per_type=2, density=0.25),
         lambda rng: gen_cluster(rng)),
        ("chains L=3", lambda rng: gen_chain_pods(rng, n_chains=2, chain_len=3, per_type=1),
         lambda rng: gen_cluster(rng, n_racks=2)),
        ("chains L=3 anti25", lambda rng: gen_chain_pods(rng, n_chains=2, chain_len=3, per_type=1, anti_fraction=0.25),
         lambda rng: gen_cluster(rng, n_racks=2)),
    ]
    for name, gen_p, gen_c in regimes:
        pred_dl = unplaced = hit = miss = 0
        for s in range(10):
            rng = random.Random(s)
            pods = gen_p(rng)
            cluster = Cluster(nodes=gen_c(rng))
            order = list(range(len(pods)))
            rng.shuffle(order)
            rq = schedule_with_requeue(cluster, pods, order, least_requested_score,
                                       rng=random.Random(s + 2), max_retries=200)
            pred = predict_deadlocks(pods)
            pred_dl += sum(1 for p in pred.values() if p["deadlock"])
            for p in rq["unplaced"]:
                unplaced += 1
                if pred[p]["deadlock"]:
                    hit += 1
                else:
                    miss += 1
        rows.append({"regime": name, "predicted": pred_dl, "unplaced": unplaced,
                     "hits": hit, "misses": miss})
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", default="")
    args = ap.parse_args()

    t0 = time.time()
    e1 = exp1()
    e2 = exp2()
    e3 = exp3()

    out = {"experiment1": e1, "experiment2": e2, "experiment3": e3}
    if args.output:
        os.makedirs(args.output, exist_ok=True)
        with open(os.path.join(args.output, "results.json"), "w") as f:
            json.dump(out, f, indent=2)

    print("=== Experiment 1: density sweep (n=20) ===")
    print(f"{'dens':>5} {'mean_gap':>9} {'grd%':>6} {'bf%':>5} {'rnd%':>6} {'opt%':>6} {'gap>0':>6}")
    for r in e1:
        print(f"{r['density']:>5.2f} {r['mean_gap']:>9.3f} {r['greedy']*100:>5.1f}% "
              f"{r['bestfit']*100:>4.1f}% {r['random']*100:>5.1f}% {r['optimal']*100:>5.1f}% "
              f"{r['gap_gt0']:>6d}")

    print("\n=== Experiment 2: chains + requeue (n=10) ===")
    print(f"{'config':>15} {'sp%':>6} {'rq%':>6} {'opt%':>6} {'chk_rq/sp':>9} {'rnds':>5} {'unrec':>6}")
    for r in e2:
        print(f"{r['config']:>15} {r['single_pass']*100:>5.1f}% {r['requeue']*100:>5.1f}% "
              f"{r['optimal']*100:>5.1f}% {r['check_ratio']:>8.1f}x {r['max_rounds']:>5d} {r['unrecoverable']:>6d}")

    print("\n=== Experiment 3: deadlock prediction (n=10) ===")
    print(f"{'regime':>18} {'pred':>5} {'unplaced':>9} {'hits':>5} {'misses':>7} {'precision':>10} {'recall':>7}")
    for r in e3:
        prec = r["hits"] / r["predicted"] * 100 if r["predicted"] else float("nan")
        rec = r["hits"] / r["unplaced"] * 100 if r["unplaced"] else float("nan")
        p = f"{prec:.0f}%" if prec == prec else "  — "
        rc = f"{rec:.0f}%" if rec == rec else "  — "
        print(f"{r['regime']:>18} {r['predicted']:>5d} {r['unplaced']:>9d} {r['hits']:>5d} "
              f"{r['misses']:>7d} {p:>10} {rc:>7}")

    print(f"\n[done in {time.time()-t0:.1f}s]")
    if args.output:
        print(f"[results written to {args.output}/results.json]")


if __name__ == "__main__":
    sys.exit(main())
