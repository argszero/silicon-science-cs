"""
ci_stats.py — mean ± 95% CI for headline metrics (quality bar: multi-run stats).

Mirrors reproduce.py EXACTLY (same seeds, same rng consumption order:
pods <- rng, cluster <- rng, order shuffle <- rng) so the CIs are
consistent with the canonical expected output.

Computes per-seed placed fractions and reports mean ± t-CI for Exp1 (density
sweep), Exp2 (chains + mutual), and the requeue variants.
"""
from __future__ import annotations

import random
import math

from sim import Cluster, least_requested_score, schedule, schedule_with_requeue
from gen import gen_cluster, gen_pods, gen_chain_pods


def t_ci(values: list[float]):
    """Student-t 95% CI for small n."""
    n = len(values)
    if n < 2:
        return values[0] if values else 0.0, 0.0
    mean = sum(values) / n
    var = sum((v - mean) ** 2 for v in values) / (n - 1)
    sd = math.sqrt(var)
    t = {5: 2.571, 9: 2.262, 19: 2.093}.get(n - 1, 1.96)
    return mean, t * sd / math.sqrt(n)


def frac_placed(pods, cluster, order, requeue=False, rq_seed=None):
    if requeue:
        r = schedule_with_requeue(cluster, pods, order, least_requested_score,
                                  rng=random.Random(rq_seed), max_retries=200)
    else:
        r = schedule(cluster, pods, order, least_requested_score)
    return r["n_placed"] / len(pods)


def exp1_seeds(d):
    """Mirror reproduce.py exp1 rng pattern."""
    vals = []
    for s in range(20):
        rng = random.Random(s)
        pods = gen_pods(rng, n_types=3, per_type=2, density=d)
        cluster = Cluster(nodes=gen_cluster(rng))
        order = list(range(len(pods)))
        rng.shuffle(order)
        vals.append(frac_placed(pods, cluster, order))
    return vals


def chain_seeds(n_chains, chain_len, anti=0.0, n=10):
    gvals, rvals = [], []
    for s in range(n):
        rng = random.Random(s)
        pods = gen_chain_pods(rng, n_chains=n_chains, chain_len=chain_len,
                              per_type=1, anti_fraction=anti)
        cluster = Cluster(nodes=gen_cluster(rng, n_racks=n_chains, nodes_per_rack=2))
        order = list(range(len(pods)))
        rng.shuffle(order)
        gvals.append(frac_placed(pods, cluster, order))
        rvals.append(frac_placed(pods, cluster, order, requeue=True, rq_seed=s + 2))
    return gvals, rvals


def mutual_seeds(n=10):
    gvals, rvals = [], []
    for s in range(n):
        rng = random.Random(s)
        pods = gen_pods(rng, n_types=3, per_type=2, density=1.0)
        cluster = Cluster(nodes=gen_cluster(rng))
        order = list(range(len(pods)))
        rng.shuffle(order)
        gvals.append(frac_placed(pods, cluster, order))
        rvals.append(frac_placed(pods, cluster, order, requeue=True, rq_seed=s + 2))
    return gvals, rvals


def main():
    print("=== Exp1: greedy placed fraction by density (mean ± 95% CI, n=20) ===")
    for d in [0.0, 0.25, 0.5, 0.75, 1.0]:
        m, ci = t_ci(exp1_seeds(d))
        print(f"  density={d:.2f}: greedy placed {m*100:5.1f}% ± {ci*100:4.1f}%")

    print("\n=== Exp2: chains greedy vs requeue (mean ± 95% CI, n=10) ===")
    for name, cfg in [
        ("2ch L=2", dict(n_chains=2, chain_len=2)),
        ("2ch L=3", dict(n_chains=2, chain_len=3)),
        ("2ch L=4", dict(n_chains=2, chain_len=4)),
        ("2ch L=3 anti25", dict(n_chains=2, chain_len=3, anti=0.25)),
    ]:
        gvals, rvals = chain_seeds(cfg["n_chains"], cfg["chain_len"], cfg.get("anti", 0.0))
        gm, gc = t_ci(gvals)
        rm, rc = t_ci(rvals)
        print(f"  {name:>15}: single-pass {gm*100:5.1f}% ± {gc*100:4.1f}% | "
              f"requeue {rm*100:5.1f}% ± {rc*100:4.1f}%")

    print("\n=== Exp2b: density=1.0 mutual (mean ± 95% CI, n=10) ===")
    gvals, rvals = mutual_seeds()
    gm, gc = t_ci(gvals)
    rm, rc = t_ci(rvals)
    print(f"  single-pass {gm*100:5.1f}% ± {gc*100:4.1f}% | requeue {rm*100:5.1f}% ± {rc*100:4.1f}%")


if __name__ == "__main__":
    main()
