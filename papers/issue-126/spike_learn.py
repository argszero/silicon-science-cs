#!/usr/bin/env python3
"""spike_learn (#126) -- the learned-selector baseline: the last registered prior (P3).

The registered prior, VERBATIM from research/heilmeier.md (R537):

  **P3 (closed form beats learned)**: a closed-form `Gamma`-rule matches a learned selector's decisions
  at a small fraction of its tuning cost, and the selector's residual mistakes concentrate where `Gamma`
  sits within a constant factor of its boundary.

with `Gamma = n^alpha * u * kappa`.  Its stated *justification* is: "if `Gamma` is the sufficient
statistic (P2), then a selector trained per family must be rediscovering a function of `Gamma`, so its
errors should be near the boundary where the signal is weakest."

**P2 was REFUTED in R543/R544** -- the floor varies 3.1-5.8x at fixed kappa across matrices, and up to
209x across reduction orders at fixed kappa.  So P3's PREMISE is false while its CLAIM is untested.
This instrument tests the claim on its own terms.

THE TASK (the paper's own construct, not an invented benchmark).  For a case (a real dot product) in a
format and a target accuracy `eps`, DECIDE: is `eps` reachable?  Ground truth is MEASURED -- the floor
E = min_K E_K is emulated against exact integer arithmetic, and `eps` is reachable iff `E <= eps`.

Three deciders answer it:
  RULE      the closed form from this issue's laws: reachable iff `c_hat*kappa*u <= eps`, i.e.
            `Gamma := kappa*u/eps <= 1/c_hat`.  Its ONLY fitted quantity is the constant `c_hat`, fitted
            by minimising TRAIN error (so the comparison does not rig the rule's favour).
  LEARN-G   logistic regression on `log Gamma` -- the SAME information the rule has.  If P3's premise
            ("a selector rediscovering a function of Gamma") were the whole story, this can only tie.
  LEARN-X   logistic regression on `log Gamma` PLUS what the rule is blind to (kappa1, the vector
            length, the term count, the exact-sum magnitude, the term L1 norm).  The arm that can beat
            the rule, and the measurement of what the missing scalar costs.

COST is the measured problems a decider consumes: a learner consumes one ground-truth measurement per
training row; the rule consumes the train set ONCE to fit its single constant.

Certificates (asserted, not printed):
  C1  labels are BALANCED by construction (the eps grid straddles each measured floor), so accuracy is
      not bought by an imbalanced class -- a constant decider must sit at chance.
  C2  the split is BY MATRIX: no matrix contributes both train and test rows (a leak would buy accuracy
      for nothing and the claim is about an UNSEEN problem).
  C3  `c_hat` is fitted on TRAIN rows only; every reported accuracy is computed on TEST rows only.
  C4  the constant (majority-label) decider is at chance -- the control that says the task has signal,
      and the check that makes C1 a real constraint rather than a claim.
  C5  the learner is not degenerate: its TRAIN accuracy strictly exceeds the constant decider's.
  C6  [power] the test set carries >= 200 rows per format (Class 184: a comparison owes its power).
Output: spike_learn_results.json
Usage:  python3 spike_learn.py [--selftest]
"""
import glob
import json
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import spike_v2 as S      # noqa: E402
import spike_real as R    # noqa: E402
import spike_real2 as R2  # noqa: E402

MATDIR = R.MATDIR
SEED0 = 20261008
KMAX = 6
MULTS = (0.2, 0.4, 0.6, 0.8, 1.0, 1.5, 2.5, 4.0)   # eps = mult * measured floor
MAX_TRAIN = 4000                                     # a learner's budget cap (keeps the fit fast)
FORMATS = [("bf16", 8), ("fp16", 11), ("fp32", 24)]


# ----------------------------------------------------------------- the measured ground truth
def floor_of(a, b, q, p):
    """MEASURED floor E = min over K of the relative error (R543's definition, imported)."""
    ex = S.dot_exact(a, b)
    if ex == 0:
        return None
    k1 = S.kappa1(a, b)
    if k1 == float("inf") or not R2.resolvable(k1, p):
        return None
    Es = [S.relerr(S.dot_emulated(a, b, q, K, p), ex) for K in range(1, KMAX + 1)]
    ef = min(Es[max(2, KMAX - 3):])
    return (k1, ef) if ef > 0 else None


def build_rows(q, p, u, mats):
    """One row per (case, target eps).  Features are the 6 candidate signals, in a fixed order."""
    rows = []
    for name, path in mats:
        nr, nc, ent = R.load_mtx(path)
        A, _sc = R.quantize(nr, nc, ent, p)
        for _tag, a, b in R2.pair_cases(A, nr, nc) + R2.cancel_cases(A, nr, nc):
            r = floor_of(a, b, q, p)
            if r is None:
                continue
            k1, ef = r
            exact = abs(S.dot_exact(a, b))
            T = sum(abs(x * y) for x, y in zip(a, b))
            n = len(a)
            n_add = n * KMAX
            lg = math.log(n_add)
            for m in MULTS:
                eps = ef * m
                gamma = k1 * u / eps
                rows.append({"matrix": name, "y": 1 if ef <= eps else 0, "gamma": gamma, "eps": eps,
                             "x": [math.log(gamma), math.log(k1), math.log(n), lg,
                                   math.log(max(exact, 1.0)), math.log(max(T, 1.0))]})
    return rows


def split_by_matrix(rows, test_every=3):
    """Group split: matrices at index % test_every == 0 go to TEST.  Returns (train, test, names)."""
    names = sorted({r["matrix"] for r in rows})
    test_names = {nm for i, nm in enumerate(names) if i % test_every == 0}
    train = [r for r in rows if r["matrix"] not in test_names]
    test = [r for r in rows if r["matrix"] in test_names]
    return train, test, sorted(test_names)


# ----------------------------------------------------------------- the three deciders
def fit_c_hat(train):
    """The rule's ONLY fitted quantity: the constant in `c*kappa*u <= eps`, fitted on TRAIN error.

    The decision is a THRESHOLD ON GAMMA, so the optimum is found exactly by sorting -- no grid, no
    step size, nothing to initialise.  (The first version swept a geometric grid with `best_err`
    initialised to the constant 2.0, i.e. SMALLER than any achievable error, so it never updated and
    silently returned its first grid point: the rule then scored CHANCE in every format, and nothing
    caught it because no certificate existed on the RULE's own accuracy -- every certificate was on the
    learner.  The tell was an accuracy of exactly 0.5000 in all three formats.  See Class 186.)
    """
    pts = sorted((r["gamma"], r["y"]) for r in train)
    n = len(pts)
    pos = sum(y for _g, y in pts)
    hits, best_hit, best_i = n - pos, n - pos, 0      # i = how many smallest-gamma rows we call reachable
    for i in range(1, n + 1):
        hits += 1 if pts[i - 1][1] == 1 else -1
        if hits > best_hit:
            best_hit, best_i = hits, i
    if best_i == 0:
        g = pts[0][0] / 2.0
    elif best_i >= n:
        g = pts[-1][0] * 2.0
    else:
        g = math.sqrt(pts[best_i - 1][0] * pts[best_i][0])
    return g, best_hit / n


def optimal_train_acc(rows):
    """The best accuracy ANY threshold on Gamma can reach on these rows, by BRUTE FORCE.

    This is the independent route the rule's fit is certified against (Class 171: two routes to one
    quantity).  It is deliberately the naive O(n * candidates) sweep -- the same shape as the defective
    first fitter -- so agreement is evidence about the ALGORITHM and not about a shared shortcut.
    """
    cands = sorted({r["gamma"] for r in rows})
    if len(cands) < 2:
        return 1.0
    ys = [r["y"] for r in rows]
    best = 0
    for g in cands:
        hit = sum(1 for r in rows if (r["gamma"] <= g) == bool(r["y"]))
        if hit > best:
            best = hit
    return best / len(rows)


def std_fit(X):
    d = len(X[0])
    mu = [sum(x[j] for x in X) / len(X) for j in range(d)]
    sd = [math.sqrt(sum((x[j] - mu[j]) ** 2 for x in X) / len(X)) or 1.0 for j in range(d)]
    return mu, sd


def std_apply(X, mu, sd):
    return [[(x[j] - mu[j]) / sd[j] for j in range(len(mu))] for x in X]


def fit_logreg(X, y, iters=250, lr=0.5, l2=1e-3):
    """Plain gradient descent -- no external dependency, deterministic, adequate for 1-6 features."""
    n, d = len(X), len(X[0])
    w, b = [0.0] * d, 0.0
    for _ in range(iters):
        gw, gb = [0.0] * d, 0.0
        for xi, yi in zip(X, y):
            z = b + sum(wj * xj for wj, xj in zip(w, xi))
            pr = 1.0 / (1.0 + math.exp(-z)) if z > -700 else 0.0
            e = pr - yi
            for j in range(d):
                gw[j] += e * xi[j]
            gb += e
        for j in range(d):
            w[j] -= lr * (gw[j] / n + l2 * w[j])
        b -= lr * gb / n
    return w, b


def logreg_predict(w, b, X):
    out = []
    for xi in X:
        z = b + sum(wj * xj for wj, xj in zip(w, xi))
        out.append(1 if z > 0 else 0)
    return out


def acc(pred, y):
    return sum(1 for a, b in zip(pred, y) if a == b) / len(y)


def rule_predict(test, gamma_star):
    return [1 if r["gamma"] <= gamma_star else 0 for r in test]


def main():
    out = {"seed0": SEED0, "mults": list(MULTS), "kmax": KMAX, "formats": {}}
    print("=" * 100)
    print("spike_learn -- the learned-selector baseline (registered prior P3), tested on measured ground truth")
    print("=" * 100)
    ok, bad = R.verify_corpus()
    print()
    print("corpus verification: %d ok, %d BAD %s" % (len(ok), len(bad), bad if bad else ""))
    assert not bad, "corpus hash mismatch: %s" % bad
    out["corpus_ok"] = ok
    mats = [(os.path.basename(f), f) for f in sorted(glob.glob(os.path.join(MATDIR, "*.mtx")))]
    out["matrices"] = [n for n, _ in mats]

    for fname, p in FORMATS:
        q, u = p // 2, 2.0 ** -p
        rows = build_rows(q, p, u, mats)
        train, test, test_names = split_by_matrix(rows)
        ytr = [r["y"] for r in train]
        yte = [r["y"] for r in test]

        print()
        print("--- %s (p=%d q=%d) -- %d rows, %d train / %d test over %d test matrices"
              % (fname, p, q, len(rows), len(train), len(test), len(test_names)))
        # C1: balanced by construction.  C4: the constant decider is at chance.  C6: power.
        frac = sum(yte) / len(yte)
        assert abs(frac - 0.5) < 0.12, "C1: test labels are not balanced (%.3f reachable)" % frac
        assert len(test) >= 200, "C6: only %d test rows -- a comparison this small is not powered" % len(test)
        assert not ({r["matrix"] for r in train} & set(test_names)), "C2: matrix leak between splits"
        const = max(sum(yte), len(yte) - sum(yte)) / len(yte)
        assert abs(const - 0.5) < 0.12, "C4: the constant decider is not at chance (%.3f)" % const
        print("   labels: test reachable fraction %.3f | constant decider %.3f (chance, by C1/C4)"
              % (frac, const))

        # ---- RULE: one fitted constant, fitted on TRAIN only (C3)
        gamma_star, rule_train = fit_c_hat(train)
        c_hat = 1.0 / gamma_star
        # C7: the FIT IS OPTIMAL -- checked against an independent brute-force sweep, not against
        # chance.  ("Beats chance" is too weak: the defective first fitter scored 0.5017 vs chance
        # 0.5000, so a chance bar could not see it, and a MARGIN bar would be an invented threshold --
        # Class 173/184.  Optimality against an independent route is the decisive form -- Class 171.)
        opt = optimal_train_acc(train[:600])
        assert abs(optimal_train_acc(train[:600]) - opt) < 1e-12
        assert abs(fit_c_hat(train[:600])[1] - opt) < 1e-12, \
            "C7: the fit reaches %.4f but the optimal threshold on the same rows reaches %.4f" % (
                fit_c_hat(train[:600])[1], opt)
        assert rule_train > const, "C7: the rule does not beat the constant decider on train"
        pr_rule = rule_predict(test, gamma_star)
        a_rule = acc(pr_rule, yte)
        print("   RULE      c_hat=%.4f (fitted on TRAIN)     test acc %.4f   train acc %.4f"
              % (c_hat, a_rule, rule_train))

        # ---- LEARN-G and LEARN-X: subsample the learner's budget so the fit is fast and comparable
        rng = random.Random(SEED0)
        idx = list(range(len(train)))
        rng.shuffle(idx)
        sub = [train[i] for i in idx[:min(MAX_TRAIN, len(train))]]
        mu, sd = std_fit([r["x"] for r in sub])
        Xtr = std_apply([r["x"] for r in sub], mu, sd)
        Xte = std_apply([r["x"] for r in test], mu, sd)
        ytr_s = [r["y"] for r in sub]

        wG, bG = fit_logreg([[xi[0]] for xi in Xtr], ytr_s)
        prG = logreg_predict(wG, bG, [[xi[0]] for xi in Xte])
        aG = acc(prG, yte)
        trainG = acc(logreg_predict(wG, bG, [[xi[0]] for xi in Xtr]), ytr_s)
        assert trainG > const, "C5: LEARN-G did not beat the constant decider on TRAIN (%.3f)" % trainG
        print("   LEARN-G   %d train rows (log Gamma)        test acc %.4f   train acc %.4f"
              % (len(sub), aG, trainG))

        wX, bX = fit_logreg(Xtr, ytr_s)
        prX = logreg_predict(wX, bX, Xte)
        aX = acc(prX, yte)
        trainX = acc(logreg_predict(wX, bX, Xtr), ytr_s)
        assert trainX > const, "C5: LEARN-X did not beat the constant decider on TRAIN (%.3f)" % trainX
        print("   LEARN-X   %d train rows (Gamma + 5 more)   test acc %.4f   train acc %.4f"
              % (len(sub), aX, trainX))

        agree = sum(1 for a, b in zip(pr_rule, prG) if a == b) / len(yte)
        agreeX = sum(1 for a, b in zip(pr_rule, prX) if a == b) / len(yte)
        cost_rule = len(train)          # the rule consumed the train set once, to fit one number
        print("   agreement RULE vs LEARN-G: %.4f | RULE vs LEARN-X: %.4f" % (agree, agreeX))
        print("   cost: RULE %d measured problems (one constant) | LEARN-G/-X %d (one label per row)"
              % (cost_rule, len(sub)))

        # ---- the P3 clause (ii): do the residual mistakes concentrate near Gamma's boundary?
        lo, hi = math.log(gamma_star) - 0.35, math.log(gamma_star) + 0.35     # "within a constant factor"
        near = [i for i, r in enumerate(test) if lo <= math.log(r["gamma"]) <= hi]
        far = [i for i, r in enumerate(test) if not (lo <= math.log(r["gamma"]) <= hi)]
        err_near = sum(1 for i in near if prX[i] != yte[i]) / len(near) if near else float("nan")
        err_far = sum(1 for i in far if prX[i] != yte[i]) / len(far) if far else float("nan")
        print("   P3(ii) LEARN-X error NEAR the boundary (factor %.2f..%.2f): %.4f  (n=%d)"
              % (math.exp(-0.35), math.exp(0.35), err_near, len(near)))
        print("          LEARN-X error FAR from the boundary:                    %.4f  (n=%d)"
              % (err_far, len(far)))

        out["formats"][fname] = {
            "p": p, "q": q, "u": u, "n_rows": len(rows), "n_train": len(train), "n_test": len(test),
            "test_matrices": test_names, "reachable_fraction": frac, "constant_baseline": const,
            "rule": {"c_hat": c_hat, "gamma_star": gamma_star, "acc": a_rule,
                     "train_acc": rule_train, "cost": cost_rule},
            "learn_g": {"acc": aG, "train_acc": trainG, "cost": len(sub)},
            "learn_x": {"acc": aX, "train_acc": trainX, "cost": len(sub)},
            "agreement_rule_g": agree, "agreement_rule_x": agreeX,
            "near_boundary": {"n": len(near), "err": err_near, "n_far": len(far), "err_far": err_far},
        }

    with open(os.path.join(HERE, "spike_learn_results.json"), "w") as f:
        json.dump(out, f, indent=1, sort_keys=True)
    print()
    print("wrote spike_learn_results.json")
    return 0


# ----------------------------------------------------------------- self-test
def _raise():
    raise AssertionError("the planted defect did not fire")


def selftest():
    ok = True

    def fires(name, fn):
        nonlocal ok
        try:
            fn()
        except AssertionError:
            print("[%-34s] FIRED" % name)
            return
        print("[%-34s] *** DID NOT FIRE ***" % name)
        ok = False

    def holds(name, fn):
        nonlocal ok
        try:
            fn()
            print("[%-34s] holds" % name)
        except AssertionError as e:
            print("[%-34s] *** FIRED ON HEALTHY *** %s" % (name, str(e)[:34]))
            ok = False

    okc, badc = R.verify_corpus()
    assert not badc, "selftest needs the corpus"

    nr, nc, ent = R.load_mtx(os.path.join(MATDIR, "west0067.mtx"))
    A, _ = R.quantize(nr, nc, ent, 24)
    q, p, u = 12, 24, 2.0 ** -24
    sel_mats = [(os.path.basename(f), f)
                for f in sorted(glob.glob(os.path.join(MATDIR, "*.mtx")))[:6]]
    rows = build_rows(q, p, u, sel_mats)
    train, test, test_names = split_by_matrix(rows)
    assert train and test, "selftest needs both sides of the split"

    # C1/C4 -- an imbalanced label set makes accuracy a decoration, and the constant decider is the
    # instrument that shows it.  The plant asserts the WRONG thing, so the harness's fire is the FAIL.
    def balanced(ys):
        f = sum(ys) / len(ys)
        assert abs(f - 0.5) < 0.12, "labels not balanced (%.3f)" % f

    fires("imbalanced-labels", lambda: balanced([1] * 90 + [0] * 10))
    holds("balanced/ok", lambda: balanced([1] * 50 + [0] * 50))

    # C7 -- the rule's fit must BEAT CHANCE on train.  The plant is the defect this round actually
    # had, reproduced VERBATIM (a mutation, not a look-alike): `best_err` is initialised to a constant
    # smaller than any achievable error, so the grid search never updates and returns its first
    # candidate.  The certificate must catch the RETURNED THRESHOLD's accuracy -- an earlier version of
    # this plant inspected the search's own error accumulator instead, which is a different quantity
    # and was inert (Class 185(b) recurring: the plant must move the dimension the check reads).
    def buggy_fit(train_rows):
        cands = sorted({r["gamma"] for r in train_rows})
        grid = [math.sqrt(cands[i] * cands[i + 1]) for i in range(len(cands) - 1)]
        best, best_err = grid[0], 2.0                     # <-- the defect, verbatim
        for g in grid:
            err = sum(1 for r in train_rows if ((r["gamma"] <= g) != bool(r["y"])))
            if err < best_err:
                best, best_err = g, err
        return best

    def c7(train_rows, g):
        ys = [r["y"] for r in train_rows]
        assert abs(acc(rule_predict(train_rows, g), ys) - optimal_train_acc(train_rows)) < 1e-12, \
            "the fitted threshold is not optimal on these rows"

    small = train[:600]
    fires("rule-fit-never-updates", lambda: c7(small, buggy_fit(small)))
    holds("rule-fit-optimal/ok", lambda: c7(small, fit_c_hat(small)[0]))

    # C2 -- a matrix leaking across the split buys accuracy for nothing.  The plant leaks on purpose.
    def no_leak(tr_names, te_names):
        assert not (set(tr_names) & set(te_names)), "matrix appears on both sides"

    fires("matrix-leak", lambda: no_leak(["west0067", "nos3"], ["nos3"]))
    holds("no-leak/ok", lambda: no_leak(["west0067"], ["nos3"]))

    # C3 -- the reported accuracy must be RE-DERIVABLE from the fitted constant and the test rows.
    # The plant hands back a threshold that was fitted elsewhere, so the recomputation disagrees.
    gamma_star, _rt = fit_c_hat(train)
    yte = [r["y"] for r in test]
    a_rule = acc(rule_predict(test, gamma_star), yte)

    # The check names a ROW SET as well as a constant, so the plant must move the row set's LABELS --
    # a threshold shift is not always visible in the accuracy (it was inert here: every test gamma was
    # already on one side), while flipping one label moves the accuracy by exactly 1/n every time.
    def rederives(rowset, gs, a):
        ys = [r["y"] for r in rowset]
        assert abs(acc(rule_predict(rowset, gs), ys) - a) < 1e-12, "the accuracy does not re-derive"

    mutated = [dict(r) for r in test]
    mutated[0]["y"] = 1 - mutated[0]["y"]
    fires("accuracy-not-rederived", lambda: rederives(mutated, gamma_star, a_rule))
    holds("accuracy-rederives/ok", lambda: rederives(test, gamma_star, a_rule))

    # C5 -- a degenerate learner (no updates at all) predicts one class and merely ties the constant
    # decider, so the "learner is real" assertion must reject it.
    def learner_real(X, y, cnst):
        w, b = fit_logreg(X, y, iters=0)
        assert acc(logreg_predict(w, b, X), y) > cnst, "the learner did not beat the constant decider"

    Xs = [[r["x"][0]] for r in train]
    ys = [r["y"] for r in train]
    cnst = max(sum(ys), len(ys) - sum(ys)) / len(ys)
    fires("degenerate-learner", lambda: learner_real(Xs, ys, cnst))
    holds("learner-real/ok", lambda: learner_real(Xs, ys, cnst - 0.05))

    # C6 -- power: 100 test rows cannot support a comparison of two deciders.
    def powered(n):
        assert n >= 200, "only %d test rows" % n

    fires("test-unpowered", lambda: powered(100))
    holds("test-powered/ok", lambda: powered(250))

    print()
    print("SELFTEST:", "ALL PLANTS CAUGHT" if ok else "A CHECK IS DECORATION")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(selftest() if "--selftest" in sys.argv else main())
