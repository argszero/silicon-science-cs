"""R397 diag: calibrate the ratio test.  Compare (a) doubled-tail p, (b) reference percentiles 2.5/97.5,
(c) a log-scale version, on a KNOWN homogeneous population; then confirm each still FIRES on a heterogeneous
one.  Both directions matter: an uncalibrated test is not evidence either way."""
import sys
import numpy as np
sys.path.insert(0, "/Users/argszero/scm/github.com/argszero/silicon-science-cs/papers/issue-87/research")
import smoke_v11 as S11

rng = np.random.default_rng(11)
N_REP = 400


def ratio(x, nb=40, ns=20):
    return S11.sd(x[:nb]) / S11.sd(x[nb:nb + ns])


def variant_stats(x, ref):
    o = ratio(x)
    p_double = 2.0 * min(np.mean(ref <= o), np.mean(ref >= o))
    lo, hi = np.percentile(ref, [2.5, 97.5])
    return p_double, (o < lo or o > hi), lo, hi, o


for name, gen in (("homog normal", lambda: rng.normal(0, 1, 120)),
                  ("homog heavy", lambda: rng.normal(0, 1, 120) * (1 + 0.5 * rng.normal(0, 1, 120) ** 2))):
    kd = ki = 0
    for _ in range(N_REP):
        x = gen()
        ref = S11.ratio_ref(x, n_rep=400, seed=int(rng.integers(0, 10**6)))
        p, outside, lo, hi, o = variant_stats(x, ref)
        kd += int(p < 0.05)
        ki += int(outside)
    print("%-13s size: doubled-tail %.3f | percentile-interval %.3f" % (name, kd / N_REP, ki / N_REP))

for name, gen in (("heterog 2x first40", lambda: (lambda y: (y.__setitem__(slice(0, 40), y[:40] * 2.0), y)[1])(rng.normal(0, 1, 120))),
                  ("heterog 1.5x first40", lambda: (lambda y: (y.__setitem__(slice(0, 40), y[:40] * 1.5), y)[1])(rng.normal(0, 1, 120)))):
    kd = ki = 0
    for _ in range(N_REP):
        x = gen()
        ref = S11.ratio_ref(x, n_rep=400, seed=int(rng.integers(0, 10**6)))
        p, outside, lo, hi, o = variant_stats(x, ref)
        kd += int(p < 0.05)
        ki += int(outside)
    print("%-20s power: doubled-tail %.3f | percentile-interval %.3f" % (name, kd / N_REP, ki / N_REP))

# log-scale variant on the same two cases
print()
for name, gen in (("homog normal", lambda: rng.normal(0, 1, 120)),
                  ("heterog 2x", lambda: (lambda y: (y.__setitem__(slice(0, 40), y[:40] * 2.0), y)[1])(rng.normal(0, 1, 120)))):
    k = 0
    for _ in range(N_REP):
        x = gen()
        lg = np.log(np.abs(x) + 1e-12)
        # a variance ratio on logs is not the sd ratio; instead compare median|dev| via a permutation
        o = np.median(np.abs(x[:40] - np.median(x[:40]))) / np.median(np.abs(x[40:] - np.median(x[40:])))
        r2 = np.random.default_rng(int(rng.integers(0, 10**6)))
        ref = []
        for _ in range(200):
            idx = r2.permutation(120)
            a, b = x[idx[:40]], x[idx[40:60]]
            ref.append(np.median(np.abs(a - np.median(a))) / np.median(np.abs(b - np.median(b))))
        ref = np.asarray(ref)
        p = 2.0 * min(np.mean(ref <= o), np.mean(ref >= o))
        k += int(p < 0.05)
    print("%-13s MAD-ratio doubled-tail size/power: %.3f" % (name, k / N_REP))
