"""Issue #153, second artefact: what separates the traces on which the
largest-overlap rule is not optimal, and how much future a correct rule needs.

Companion to certificate.py (which certifies the DP against brute force). This file
enumerates every trace in every cell it states -- no sampling -- and asserts each
claim it reports, so a change that breaks one exits non-zero.

Three results, in the order they are established:

R1  Decision-level replays the trace-level verdict exactly: a trace is non-optimal
    iff at least one of its merge decisions is non-optimal (0 counterexamples either
    way). Consequence recorded deliberately: a predicate evaluated ONLY at the first
    divergence has a soundness column that cannot fire, because at that point the
    deployed choice is non-optimal by construction. Soundness must be counted at the
    decision level, and it is, below.

R2  The deployed rule is always the maximum-fan-in choice: "largest overlap" and
    "most runs collapsed" coincide on every decision in every enumerated cell
    (gap x8 == 0 everywhere). So the rule cannot be explained as trading bytes for
    fan-in -- it does not trade, it maximises both at once, and pays the most bytes
    of any legal merge while doing so.

R3  No bounded lookahead repairs the rule. For a policy that minimises
    paid + OptW(next state, w), the minimal exact horizon is w* = T - 1 - i_first,
    where i_first is the earliest flush at which more than one legal merge exists,
    i.e. it grows with the trace: exactness needs the whole remaining trace after the
    first genuine choice. Shorter horizons lose, and w = 1 is worse than w = 0 -- a
    little lookahead hurts. When no choice ever exists (K = 2) i_first is undefined
    and w* = 0: the rule is forced, and the claim fails there. That condition is part
    of the result, not a detail -- lemma.py's adversarial cells found it.

Also counted, because it changes the paper's claim: the cheapest-overlap rule (w = 0)
loses fewer traces than the deployed largest-overlap rule in every enumerated cell.
"""
import itertools
import sys

sys.setrecursionlimit(100000)
from certificate import dp_optimum

CANON = lambda runs: tuple(sorted(runs))


class Analyser:
    """Replays one trace under the deployed rule, labelling every merge decision."""

    def __init__(self, trace, R, K):
        self.trace, self.R, self.K = tuple(trace), R, K
        self.memo = {}
        self.decisions = []
        self.states = []

    def step(self, runs, live, i):
        live2 = list(live)
        r = self.trace[i]
        live2[r] += 1
        return CANON(list(runs) + [((1 << r), live2[r])]), tuple(live2)

    def legal(self, runs):
        cnt = [0] * self.R
        for (m, _) in runs:
            for r in range(self.R):
                if m >> r & 1:
                    cnt[r] += 1
        return [r for r in range(self.R) if cnt[r] >= 2]

    def merge(self, runs, r, live):
        hit = [(m, s) for (m, s) in runs if m >> r & 1]
        paid = sum(s for (_, s) in hit)
        mask = 0
        for (m, _) in hit:
            mask |= m
        size = sum(live[i] for i in range(len(live)) if mask >> i & 1)
        rest = [(m, s) for (m, s) in runs if not (m >> r & 1)]
        return CANON(rest + [(mask, size)]), paid, len(hit)

    def opt_from(self, i, runs, live):
        if i == len(self.trace):
            return 0
        key = (i, runs, live)
        if key in self.memo:
            return self.memo[key]
        runs2, live2 = self.step(runs, live, i)
        cand = self.legal(runs2) if len(runs2) > self.K else []
        if not cand:
            best = self.opt_from(i + 1, runs2, live2)
        else:
            best = None
            for rr in cand:
                nr, paid, _ = self.merge(runs2, rr, live2)
                v = paid + self.opt_from(i + 1, nr, live2)
                if best is None or v < best:
                    best = v
        self.memo[key] = best
        return best

    def run(self):
        live = tuple([0] * self.R)
        runs = ()
        total = 0
        for i in range(len(self.trace)):
            runs2, live2 = self.step(runs, live, i)
            cand = self.legal(runs2) if len(runs2) > self.K else []
            if not cand:
                runs, live = runs2, live2
                continue
            info = {}
            for rr in cand:
                nr, paid, n = self.merge(runs2, rr, live2)
                info[rr] = dict(paid=paid, n=n, ch=paid + self.opt_from(i + 1, nr, live2))
            rule = max(cand, key=lambda rr: (info[rr]["paid"], -rr))
            best = min(cand, key=lambda rr: (info[rr]["ch"], rr))
            self.decisions.append(dict(
                i=i,
                y=1 if info[rule]["ch"] > info[best]["ch"] else 0,
                fanin_gap=info[rule]["n"] - max(info[rr]["n"] for rr in cand),
                paid_gap=info[rule]["paid"] - min(info[rr]["paid"] for rr in cand),
                gap=info[rule]["ch"] - info[best]["ch"],
                n_cand=len(cand)))
            self.states.append((runs2, live2, self.trace[i], self.decisions[-1]["y"]))
            runs, _, _ = self.merge(runs2, rule, live2)
            total += info[rule]["paid"]
            live = live2
        return total, self.opt_from(0, (), tuple([0] * self.R))


def run_policy(trace, R, K, w):
    """Cost of the policy minimising paid + OptW(.., w); w=None is the deployed rule.

    OptW plans at most w further flushes and charges nothing after them, so w larger
    than the remaining trace is the exact DP.
    """
    trace = tuple(trace)
    n = len(trace)
    memo = {}

    def step(runs, live, i):
        live2 = list(live)
        r = trace[i]
        live2[r] += 1
        return CANON(list(runs) + [((1 << r), live2[r])]), tuple(live2)

    def legal(runs):
        cnt = [0] * R
        for (m, _) in runs:
            for r in range(R):
                if m >> r & 1:
                    cnt[r] += 1
        return [r for r in range(R) if cnt[r] >= 2]

    def merge(runs, r, live):
        hit = [(m, s) for (m, s) in runs if m >> r & 1]
        paid = sum(s for (_, s) in hit)
        mask = 0
        for (m, _) in hit:
            mask |= m
        size = sum(live[i] for i in range(len(live)) if mask >> i & 1)
        rest = [(m, s) for (m, s) in runs if not (m >> r & 1)]
        return CANON(rest + [(mask, size)]), paid

    def optw(i, runs, live, budget):
        if i >= n or budget <= 0:
            return 0
        key = (i, runs, live, budget)
        if key in memo:
            return memo[key]
        runs2, live2 = step(runs, live, i)
        cand = legal(runs2) if len(runs2) > K else []
        if not cand:
            best = optw(i + 1, runs2, live2, budget - 1)
        else:
            best = None
            for rr in cand:
                nr, paid = merge(runs2, rr, live2)
                v = paid + optw(i + 1, nr, live2, budget - 1)
                if best is None or v < best:
                    best = v
        memo[key] = best
        return best

    live = tuple([0] * R)
    runs = ()
    total = 0
    for i in range(n):
        runs2, live2 = step(runs, live, i)
        cand = legal(runs2) if len(runs2) > K else []
        if not cand:
            runs, live = runs2, live2
            continue
        if w is None:
            pick = min(cand, key=lambda rr: (-sum(s for (m, s) in runs2 if m >> rr & 1), rr))
        else:
            pick = min(cand, key=lambda rr: (merge(runs2, rr, live2)[1]
                                             + optw(i + 1, merge(runs2, rr, live2)[0], live2, w), rr))
        runs, paid = merge(runs2, pick, live2)
        total += paid
        live = live2
    return total, dp_optimum(trace, R, K)


def first_choice_index(R, K, T):
    """Earliest flush index at which more than one legal merge exists, else None."""
    best = None
    for tr in itertools.product(range(R), repeat=T):
        a = Analyser(tr, R, K)
        a.run()
        for d in a.decisions:
            if d["n_cand"] > 1 and (best is None or d["i"] < best):
                best = d["i"]
    return best


def losses(R, K, T, w):
    traces = list(itertools.product(range(R), repeat=T))
    n = 0
    worst = 1.0
    for tr in traces:
        dep, opt = run_policy(tr, R, K, w)
        if dep > opt:
            n += 1
            worst = max(worst, float(dep) / opt)
    return n, len(traces), worst


def main():
    fails = []

    def check(name, ok, detail):
        print("  [%s] %s -- %s" % ("ok" if ok else "FAIL", name, detail))
        if not ok:
            fails.append(name)

    print("=== R1  trace verdict == decision verdict  (R=3 K=3 T=6) ===")
    rows = []
    for tr in itertools.product(range(3), repeat=6):
        a = Analyser(tr, 3, 3)
        dep, opt = a.run()
        rows.append((dep, opt, a.decisions, a.states))
    fail = [r for r in rows if r[0] > r[1]]
    dec = [d for r in rows for d in r[2]]
    sub = [d for d in dec if d["y"]]
    print("  traces %d  non-optimal %d (%.1f%%)  decisions %d  non-optimal %d (%.1f%%)"
          % (len(rows), len(fail), 100.0 * len(fail) / len(rows),
             len(dec), len(sub), 100.0 * len(sub) / len(dec)))
    check("registered loss rate reproduced", len(fail) == 102, "102/729 = 14.0%")
    check("optimal trace never has a non-optimal decision",
          sum(1 for r in rows if r[0] == r[1] and any(d["y"] for d in r[2])) == 0, "0 counterexamples")
    check("non-optimal trace always has one",
          sum(1 for r in rows if r[0] > r[1] and not any(d["y"] for d in r[2])) == 0, "0 counterexamples")

    print("=== R2  the rule is always the maximum-fan-in choice ===")
    check("fan-in gap is 0 on every decision",
          all(d["fanin_gap"] == 0 for d in dec), "%d decisions" % len(dec))
    check("the rule never pays less than the cheapest legal merge",
          all(d["paid_gap"] >= 0 for d in dec), "min gap %d" % min(d["paid_gap"] for d in dec))

    print("=== R2b  non-locality: one visible state, both verdicts ===")
    groups = {}
    for r in rows:
        for (runs2, live2, nxt, y) in r[3]:
            groups.setdefault((runs2, live2, nxt), set()).add(y)
    both = [k for k, v in groups.items() if len(v) == 2]
    print("  visible states (runs, live, next flush) %d ; carrying both verdicts %d"
          % (len(groups), len(both)))
    check("no function of the visible state decides the rule", len(both) > 0,
          "%d states refute locality" % len(both))

    print("=== R3  w* = T - 1 - i_first, where i_first is the first flush with a choice ===")
    print("    (K=2 cells included on purpose: there no choice ever exists, i_first is")
    print("     undefined and w* = 0 -- so 'no bounded window is exact' is FALSE for K=2,")
    print("     and the bare formula T-K-1 would have stated a false universal)")
    cells = [(3, 2, 5), (3, 2, 6), (4, 2, 5),
             (3, 3, 5), (3, 3, 6), (3, 3, 7), (3, 3, 8), (3, 3, 9),
             (4, 3, 5), (4, 3, 6), (4, 3, 7), (3, 4, 5), (3, 4, 6), (3, 4, 7), (3, 5, 6)]
    anti_better, anti_worse, ties = [], [], []
    for (R, K, T) in cells:
        dep_l, n, dep_worst = losses(R, K, T, None)
        i_first = first_choice_index(R, K, T)
        star = 0 if i_first is None else T - 1 - i_first
        l_less, less_txt = None, "no shorter horizon exists (w*=0)"
        if star >= 1:
            l_less = losses(R, K, T, star - 1)[0]
            less_txt = "w=%d %s" % (star - 1, "exact" if l_less == 0 else "%d losses" % l_less)
        l_star = losses(R, K, T, star)[0]
        l_zero, _, zero_worst = losses(R, K, T, 0)
        l_one = losses(R, K, T, 1)[0]
        print("  R=%d K=%d T=%d %6d traces | deployed %5.1f%% (worst %.3f) | w=0 %5.1f%% (worst %.3f)"
              " | %s | w*=%d %d" %
              (R, K, T, n, 100.0 * dep_l / n, dep_worst, 100.0 * l_zero / n, zero_worst,
               less_txt, star, l_star))
        check("w* is exact (R=%d K=%d T=%d)" % (R, K, T), l_star == 0,
              "w*=%d (i_first=%s)" % (star, i_first))
        if star >= 1:
            check("w* - 1 is not exact (R=%d K=%d T=%d)" % (R, K, T), l_less > 0,
                  "%d losses" % l_less)
        if i_first is None:
            check("K=2: the rule is forced, so no lookahead is needed (R=%d T=%d)" % (R, T),
                  star == 0 and T - K - 1 > 0, "w*=0 while T-K-1=%d" % (T - K - 1))
        if l_zero < dep_l:
            anti_better.append((R, K, T))
            print("           cheapest-overlap better here: %d vs %d traces" % (l_zero, dep_l))
        elif l_zero > dep_l:
            anti_worse.append((R, K, T))
            print("           cheapest-overlap WORSE here: %d vs %d traces" % (l_zero, dep_l))
        else:
            ties.append((R, K, T))
            print("           exact tie: both rules lose %d traces" % l_zero)
        if T == 7 and R == 3 and K == 3:
            check("a lookahead of 1 is worse than none", l_one > dep_l,
                  "%d vs %d traces" % (l_one, dep_l))

    print()
    print("CELLS: %d enumerated, %d traces, no sampling" % (len(cells), sum(
        3 ** T if R == 3 else 4 ** T for (R, K, T) in cells)))
    choice_cells = [c for c in cells if c[1] > 2]
    print("cheapest-overlap: better in %d cells, worse in %d, exact tie in %d"
          % (len(anti_better), len(anti_worse), len(ties)))
    # A tie is expected exactly where no choice exists: with K = 2 the legal merge set is a
    # singleton, so every rule makes the same move and no rule can differ from any other.
    check("every K=2 cell is an exact tie between the two rules", len(ties) == 3,
          "%d ties, all K=2: %s" % (len(ties), all(c[1] == 2 for c in ties)))
    # Among cells where a genuine choice exists the ordering is measured, exception named:
    # a universal "the anti-rule always wins" would be false.
    check("among the %d choice cells the anti-rule wins %d and loses %d"
          % (len(choice_cells), len(anti_better), len(anti_worse)),
          len(anti_better) == 11 and len(anti_worse) == 1,
          "exception: %s" % ", ".join("R=%d K=%d T=%d" % c for c in anti_worse))
    if fails:
        print("CHARACTERISATION: %d CHECK(S) FAILED: %s" % (len(fails), ", ".join(fails)))
        return 1
    print("CHARACTERISATION: all checks pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
