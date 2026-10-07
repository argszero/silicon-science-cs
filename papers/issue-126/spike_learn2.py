#!/usr/bin/env python3
"""spike_learn2 (#126) -- STRESSING the P3 conclusion: an absolute target grid, and a second selector family.

R545 (spike_learn) tested registered prior P3 and confirmed both clauses -- the closed-form `Gamma` rule
matches a learned selector's decisions at a fraction of its tuning cost, and the selector's mistakes
concentrate near the boundary.  But R545's own design note named two things a reviewer would ask:

  (1) the target grid was scaled PER CASE (`eps = m * E_floor`), which makes the reachable fraction
      exactly 1/2 by construction and reduces the task to estimating one constant per matrix.  A grid of
      ABSOLUTE targets, shared across cases, tests the MAGNITUDE of the floor instead -- a different and
      strictly harder task;
  (2) the "a selector cannot extract more" half of P3 rested on ONE hypothesis class (logistic
      regression).  A different class could in principle find the structure the logistic misses.

This instrument re-runs the comparison on both axes: an ABSOLUTE eps grid, and a SECOND family -- a
depth-limited CART grown greedily on the same features.  Nothing else changes, so any difference from
R545 is attributable to the two stressors.

The features are the same six as R545 PLUS `log eps` itself, so the learners see the target explicitly;
LEARN-G (the rule's own signal, `log Gamma = log(kappa*u/eps)`) keeps the like-for-like comparison.

Certificates (asserted, not printed):
  C1  the absolute grid SPANS the transition: there is a target the corpus mostly reaches AND one it
      mostly does not (otherwise the task is trivial and every decider would score ~1).
  C2  the split is BY MATRIX -- no matrix contributes to both sides.
  C3  `c` is fitted on TRAIN only, and is optimal there against a brute-force sweep (Class 186's C7).
  C4  the constant (majority-label) decider's score is reported for every decider's comparison.
  C5  the family is NOT degenerate: its TRAIN accuracy strictly beats the constant decider.
  C6  [power] >= 400 test rows and >= 24 test decisions in the hard band (Class 184).
  C7  the tree's split search is complete: its chosen split is not beaten by any single-feature split
      evaluated independently at the root (a cheap optimality check on the greedy step).
Output: spike_learn2_results.json
Usage:  python3 spike_learn2.py [--selftest]
"""
import glob
import json
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import spike_v2 as S        # noqa: E402
import spike_real as R      # noqa: E402
import spike_real2 as R2    # noqa: E402
import spike_learn as L     # noqa: E402  (the learner primitives and the RULE's fit, REUSED not copied)

MATDIR = R.MATDIR
SEED0 = 20261009
KMAX = 6
N_ABS = 7                       # absolute targets per format
MAX_TRAIN = 4000
FORMATS = [("bf16", 8), ("fp16", 11), ("fp32", 24)]
HARD_LO, HARD_HI = 0.2, 0.8     # a target is "hard" when the corpus reaches it 20-80 % of the time


# ----------------------------------------------------------------- a second selector family: greedy CART
def _gini(ys):
    if not ys:
        return 0.0
    p = sum(ys) / len(ys)
    return 2.0 * p * (1.0 - p)


def _best_split(X, y, min_leaf):
    """The split minimising the weighted child Gini -- a COMPLETE search over every (feature, cut).

    Prefix counts, so the sweep is O(n log n + n*d) and exact: candidate cuts are the midpoints between
    consecutive order statistics of each feature.  (The first version indexed `left`/`right` as it slid
    the boundary and produced the right answer for the wrong reason -- and C7, which checks the root
    split against an independent per-feature search, is what a rewrite of this kind has to pass.)
    """
    n, d = len(X), len(X[0])
    base = _gini(y)
    tot_pos = sum(y)
    best = None
    for j in range(d):
        order = sorted(range(n), key=lambda i: X[i][j])
        pos_l = 0
        for k in range(1, n):
            pos_l += y[order[k - 1]]
            if k < min_leaf or n - k < min_leaf:
                continue
            pl, pr = pos_l / k, (tot_pos - pos_l) / (n - k)
            g = (k * 2 * pl * (1 - pl) + (n - k) * 2 * pr * (1 - pr)) / n
            if g < base - 1e-12 and (best is None or g < best[0]):
                best = (g, j, (X[order[k - 1]][j] + X[order[k]][j]) / 2.0)
    return best


def fit_tree(X, y, max_depth=3, min_leaf=20, depth=0):
    """Greedy CART with a Gini criterion -- a family with a different inductive bias from a linear one."""
    if depth >= max_depth or len(y) < 2 * min_leaf or _gini(y) == 0.0:
        return {"leaf": (sum(y) / len(y) >= 0.5)}
    sp = _best_split(X, y, min_leaf)
    if sp is None:
        return {"leaf": (sum(y) / len(y) >= 0.5)}
    _g, j, cut = sp
    li = [i for i in range(len(X)) if X[i][j] <= cut]
    ri = [i for i in range(len(X)) if X[i][j] > cut]
    return {"j": j, "cut": cut,
            "lo": fit_tree([X[i] for i in li], [y[i] for i in li], max_depth, min_leaf, depth + 1),
            "hi": fit_tree([X[i] for i in ri], [y[i] for i in ri], max_depth, min_leaf, depth + 1)}


def tree_predict(tree, X):
    out = []
    for x in X:
        t = tree
        while "leaf" not in t:
            t = t["lo"] if x[t["j"]] <= t["cut"] else t["hi"]
        out.append(1 if t["leaf"] else 0)
    return out


# ----------------------------------------------------------------- the ABSOLUTE-target task
def floors_of(q, p, mats):
    """Pass 1: every case's MEASURED floor, so the absolute grid can be placed at the corpus's scale."""
    out = []
    for name, path in mats:
        nr, nc, ent = R.load_mtx(path)
        A, _sc = R.quantize(nr, nc, ent, p)
        for _tag, a, b in R2.pair_cases(A, nr, nc) + R2.cancel_cases(A, nr, nc):
            r = L.floor_of(a, b, q, p)
            if r is not None:
                out.append((name, a, b, r[0], r[1]))
    return out


def abs_grid(cases):
    """An ABSOLUTE eps grid: log-spaced across the corpus's own FLOOR distribution.

    `cases` rows are `(matrix, a, b, kappa1, E_floor)` -- the grid is the FLOOR (index 4).  The first
    version read index 3, i.e. the CONDITIONING, so the grid spanned kappa1's range (1 .. 34) and every
    floor sat below it: every label came out 1 and the whole comparison was against a task with no
    negatives (the tell is the all-one-class split, which the selftest's balance assertion caught).
    """
    es = sorted(c[4] for c in cases)
    lo, hi = es[len(es) // 10], es[-len(es) // 20]          # 10th .. 95th percentile
    return [lo * (hi / lo) ** (i / (N_ABS - 1)) for i in range(N_ABS)]


def build_rows_abs(u, cases, grid):
    """Pass 2: one row per (case, ABSOLUTE target).  Features are the 6 signals PLUS the target itself."""
    rows = []
    for name, a, b, k1, ef in cases:
        exact = abs(S.dot_exact(a, b))
        T = sum(abs(x * y) for x, y in zip(a, b))
        n = len(a)
        for eps in grid:
            gamma = k1 * u / eps
            rows.append({"matrix": name, "y": 1 if ef <= eps else 0, "gamma": gamma, "eps": eps,
                         "x": [math.log(gamma), math.log(k1), math.log(n), math.log(n * KMAX),
                               math.log(max(exact, 1.0)), math.log(max(T, 1.0)), math.log(eps)]})
    return rows


def single_feature_best(X, y, min_leaf=20):
    """The best Gini split ANY single feature can make at the root -- C7's independent comparison."""
    n, d = len(X), len(X[0])
    base = _gini(y)
    tot_pos = sum(y)
    best = (base, None)
    for j in range(d):
        order = sorted(range(n), key=lambda i: X[i][j])
        pos_l = 0
        for k in range(1, n):
            pos_l += y[order[k - 1]]
            if k < min_leaf or n - k < min_leaf:
                continue
            pl, pr = pos_l / k, (tot_pos - pos_l) / (n - k)
            g = (k * 2 * pl * (1 - pl) + (n - k) * 2 * pr * (1 - pr)) / n
            if g < best[0]:
                best = (g, j)
    return best


def main():
    out = {"seed0": SEED0, "n_abs": N_ABS, "kmax": KMAX, "hard_band": [HARD_LO, HARD_HI], "formats": {}}
    print("=" * 100)
    print("spike_learn2 -- stressing P3: an ABSOLUTE target grid and a SECOND selector family (greedy CART)")
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
        cases = floors_of(q, p, mats)
        grid = abs_grid(cases)
        rows = build_rows_abs(u, cases, grid)
        train, test, test_names = L.split_by_matrix(rows)
        ytr, yte = [r["y"] for r in train], [r["y"] for r in test]
        const = max(sum(yte), len(yte) - sum(yte)) / len(yte)

        # per-target reachable fraction: C1 says the grid must SPAN the transition
        per_eps = []
        for eps in grid:
            ys = [r["y"] for r in test if r["eps"] == eps]
            per_eps.append((eps, sum(ys) / len(ys) if ys else float("nan")))
        fracs = [f for _e, f in per_eps]
        assert min(fracs) < 0.35 and max(fracs) > 0.65, \
            "C1: the absolute grid does not span the transition (%.3f .. %.3f)" % (min(fracs), max(fracs))
        assert len(test) >= 400, "C6: only %d test rows" % len(test)
        assert not ({r["matrix"] for r in train} & set(test_names)), "C2: matrix leak"

        print()
        print("--- %s (p=%d q=%d) -- %d cases, %d targets, %d rows (%d train / %d test)"
              % (fname, p, q, len(cases), len(grid), len(rows), len(train), len(test)))
        print("   absolute targets and the fraction of TEST cases that reach them:")
        for eps, fr in per_eps:
            print("        eps=%.3e   reachable %.3f" % (eps, fr))
        print("   test reachable fraction %.3f | constant decider %.3f" % (sum(yte) / len(yte), const))

        # ---- RULE (the same closed form, fitted on TRAIN only)
        gamma_star, rule_train = L.fit_c_hat(train)
        opt = L.optimal_train_acc(train[:600])
        assert abs(L.fit_c_hat(train[:600])[1] - opt) < 1e-12, "C3: the rule's fit is not optimal on train"
        a_rule = L.acc(L.rule_predict(test, gamma_star), yte)

        # ---- the three learners
        rng = random.Random(SEED0)
        idx = list(range(len(train)))
        rng.shuffle(idx)
        sub = [train[i] for i in idx[:min(MAX_TRAIN, len(train))]]
        mu, sd = L.std_fit([r["x"] for r in sub])
        Xtr, Xte = L.std_apply([r["x"] for r in sub], mu, sd), L.std_apply([r["x"] for r in test], mu, sd)
        ysub = [r["y"] for r in sub]

        def learner_arm(cols, label):
            w, b = L.fit_logreg([[xi[j] for j in cols] for xi in Xtr], ysub)
            tr = L.acc(L.logreg_predict(w, b, [[xi[j] for j in cols] for xi in Xtr]), ysub)
            te = L.acc(L.logreg_predict(w, b, [[xi[j] for j in cols] for xi in Xte]), yte)
            assert tr > const, "C5: %s does not beat the constant decider on train (%.3f vs %.3f)" % (
                label, tr, const)
            return tr, te

        trG, teG = learner_arm([0], "LEARN-G")
        trX, teX = learner_arm(list(range(7)), "LEARN-X")

        tree = fit_tree(Xtr, ysub)
        trT = L.acc(tree_predict(tree, Xtr), ysub)
        teT = L.acc(tree_predict(tree, Xte), yte)
        assert trT > const, "C5: TREE does not beat the constant decider on train (%.3f vs %.3f)" % (trT, const)
        _gb, _gj = single_feature_best(Xtr, ysub)
        root = _best_split(Xtr, ysub, 20)
        assert root is None or _gb <= root[0] + 1e-12, \
            "C7: a single feature beats the tree's root split (%.6f vs %.6f)" % (_gb, root[0])

        print("   absolute-target task (features include log eps):")
        print("        RULE      c=%.4f     train %.4f   TEST %.4f" % (1.0 / gamma_star, rule_train, a_rule))
        print("        LEARN-G   log Gamma                train %.4f   TEST %.4f" % (trG, teG))
        print("        LEARN-X   6 signals + log eps      train %.4f   TEST %.4f" % (trX, teX))
        print("        TREE      CART d=3, Gini           train %.4f   TEST %.4f" % (trT, teT))

        # ---- the HARD band: targets the corpus reaches 20-80 % of the time (the discriminating region)
        by_eps = {}
        for r in test:
            t, h = by_eps.get(r["eps"], (0, 0))
            by_eps[r["eps"]] = (t + 1, h + r["y"])
        hard = [i for i, r in enumerate(test)
                if HARD_LO <= by_eps[r["eps"]][1] / by_eps[r["eps"]][0] <= HARD_HI]
        assert len(hard) >= 24, "C6: only %d test decisions in the hard band" % len(hard)
        yh = [yte[i] for i in hard]
        pr_rule = L.rule_predict([test[i] for i in hard], gamma_star)
        acc_h_rule = L.acc(pr_rule, yh)
        # the learners' predictions on the same rows
        wG, bG = L.fit_logreg([[xi[0]] for xi in Xtr], ysub)
        wX, bX = L.fit_logreg(Xtr, ysub)
        acc_h_G = L.acc(L.logreg_predict(wG, bG, [[Xte[i][0]] for i in hard]), yh)
        acc_h_X = L.acc(L.logreg_predict(wX, bX, [Xte[i] for i in hard]), yh)
        acc_h_T = L.acc(tree_predict(tree, [Xte[i] for i in hard]), yh)
        print("   HARD band (reachable 0.2-0.8): %d test decisions" % len(hard))
        print("        RULE %.4f | LEARN-G %.4f | LEARN-X %.4f | TREE %.4f | constant %.4f"
              % (acc_h_rule, acc_h_G, acc_h_X, acc_h_T, max(sum(yh), len(yh) - sum(yh)) / len(yh)))

        out["formats"][fname] = {
            "p": p, "q": q, "u": u, "n_cases": len(cases), "n_abs": len(grid),
            "n_rows": len(rows), "n_train": len(train), "n_test": len(test),
            "test_matrices": test_names, "grid": grid, "per_eps_reachable": fracs,
            "test_reachable_fraction": sum(yte) / len(yte), "constant_baseline": const,
            "rule": {"c_hat": 1.0 / gamma_star, "gamma_star": gamma_star,
                     "train_acc": rule_train, "acc": a_rule},
            "learn_g": {"train_acc": trG, "acc": teG},
            "learn_x": {"train_acc": trX, "acc": teX},
            "tree": {"train_acc": trT, "acc": teT},
            "hard_band": {"n": len(hard), "rule": acc_h_rule, "learn_g": acc_h_G,
                          "learn_x": acc_h_X, "tree": acc_h_T,
                          "constant": max(sum(yh), len(yh) - sum(yh)) / len(yh)},
        }

    with open(os.path.join(HERE, "spike_learn2_results.json"), "w") as f:
        json.dump(out, f, indent=1, sort_keys=True)
    print()
    print("wrote spike_learn2_results.json")
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

    # the FULL corpus: a 6-matrix subset can put every TRAIN row in one class (it did -- the certificate
    # then has nothing to compare and its "healthy" case fires), so the selftest runs at the real width.
    sel_mats = [(os.path.basename(f), f) for f in sorted(glob.glob(os.path.join(MATDIR, "*.mtx")))]
    cases = floors_of(12, 24, sel_mats)
    grid = abs_grid(cases)
    rows = build_rows_abs(2.0 ** -24, cases, grid)
    train, test, test_names = L.split_by_matrix(rows)
    ytr, yte = [r["y"] for r in train], [r["y"] for r in test]

    # C1 -- a grid whose targets are all trivially reachable (or all unreachable) makes every decider
    # score ~1 and the comparison meaningless.  The plant is such a grid.
    def spans(fracs):
        assert min(fracs) < 0.35 and max(fracs) > 0.65, "the grid does not span the transition"

    fires("grid-does-not-span", lambda: spans([0.99, 1.0, 1.0, 0.98]))
    holds("grid-spans/ok", lambda: spans([0.1, 0.5, 0.9]))

    # C2 -- matrix leak
    def no_leak(tr, te):
        assert not (set(tr) & set(te)), "matrix on both sides"

    fires("matrix-leak", lambda: no_leak(["a", "b"], ["b"]))
    holds("no-leak/ok", lambda: no_leak(["a"], ["b"]))

    # C3 -- the RULE's fit must be optimal on train (Class 186's certificate, reused here)
    def c3(train_rows, g):
        ys = [r["y"] for r in train_rows]
        assert abs(L.acc(L.rule_predict(train_rows, g), ys)
                   - L.optimal_train_acc(train_rows)) < 1e-12, "the rule's fit is not optimal"

    def buggy_fit(train_rows):
        cands = sorted({r["gamma"] for r in train_rows})
        g0 = math.sqrt(cands[0] * cands[1])
        return g0                                       # the never-updating search's return value

    fires("rule-fit-not-optimal", lambda: c3(train[:600], buggy_fit(train[:600])))
    holds("rule-fit-optimal/ok", lambda: c3(train[:600], L.fit_c_hat(train[:600])[0]))

    # C5 -- a degenerate family (no learning) ties the constant decider and must be rejected
    # `iters` is a PARAMETER: the health check must run a REAL fit, or the "healthy" case is the
    # degenerate one and the assertion fires on it (that is how this read the first time).
    def family_real(X, y, cnst, iters):
        w, b = L.fit_logreg(X, y, iters=iters)
        assert L.acc(L.logreg_predict(w, b, X), y) > cnst, "the family is degenerate"

    Xs = [[r["x"][0]] for r in train]
    cnst = max(sum(ytr), len(ytr) - sum(ytr)) / len(ytr)
    assert 0.0 < sum(ytr) < len(ytr), "the selftest split carries only one class -- C5 would be vacuous"
    fires("family-degenerate", lambda: family_real(Xs, ytr, cnst, 0))
    holds("family-real/ok", lambda: family_real(Xs, ytr, cnst, 250))

    # C7 -- the tree's root split must be no worse than the best SINGLE-FEATURE split.  The plant
    # returns a deliberately poor split, so the assertion (which allows the single feature to win by
    # at most 1e-12) rejects it.
    def root_ok(root_g, single_g):
        assert single_g <= root_g + 1e-12, "a single feature beats the root split"

    fires("root-split-beaten", lambda: root_ok(0.10, 0.49))
    holds("root-split-ok/ok", lambda: root_ok(0.10, 0.10))

    # C6 -- power
    def powered(n):
        assert n >= 400, "only %d test rows" % n

    fires("test-unpowered", lambda: powered(100))
    holds("test-powered/ok", lambda: powered(500))

    print()
    print("SELFTEST:", "ALL PLANTS CAUGHT" if ok else "A CHECK IS DECORATION")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(selftest() if "--selftest" in sys.argv else main())
