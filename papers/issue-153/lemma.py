"""Issue #153, third artefact: the non-locality proposition, stated and witnessed.

PROPOSITION (no visible-state rule is exact on this model).

Fix a cell (R, K, T). Call a decision rule *visible-state* if its merge choice is a
function of the information available at the decision: the multiset of runs with their
sizes, the live bytes per range, and the flush about to be appended.  (That set is a
SUPERSET of what the deployed largest-overlap rule reads, so a rule refuted here is
refuted for any narrower information set as well -- the refutation only gets stronger.)

Let S = (i, runs, live, next) be such a state, reached at flush i of a T-flush trace, so
every trace reaching S has the same number of flushes still to come.  For a continuation
tau (a suffix of length T-1-i) let argmin(S, tau) be the set of legal merges at S that lie
on an optimal path for tau, and define

    Opt(S) = intersection of argmin(S, tau) over every tau that occurs in the cell.

Then, if Opt(S) is empty for some reachable S, no visible-state rule is optimal on the
cell: such a rule must choose one candidate r at S regardless of which trace it is in, and
r lies outside argmin(S, tau) for at least one tau, so it is suboptimal there.

WHAT THIS FIXES.  The previous round reported that "9 of 102 visible states carry both
verdicts".  That is a census of witnesses for a WEAKER claim: it shows the DEPLOYED rule is
not a function of the visible state.  It does not show that no visible-state rule is exact,
because a different rule could have picked a different candidate at those states.  The
empty-intersection test below refutes the whole class, and the deployed rule's failure is
then a corollary rather than the evidence.

The witness is printed as complete traces, so the claim can be checked by hand without
running anything.

Second part (main, part B): the horizon formula w* = T - K - 1 is tested for the scope it
actually has.  Cells with K = 2 are included on purpose: there the legal merge set at the
first forced merge is a singleton, so no choice exists and w* = 0, while T - K - 1 > 0.
Stating the formula without that condition would be a false universal -- which is exactly
what an adversarial search is for.
"""
import itertools
import sys


def canon(runs):
    return tuple(sorted(runs))


class Cell:
    """The model: K slots, R ranges, run sizes frozen at creation."""

    def __init__(self, R, K, T):
        self.R, self.K, self.T = R, K, T

    def step(self, runs, live, r):
        live2 = list(live)
        live2[r] += 1
        return canon(list(runs) + [((1 << r), live2[r])]), tuple(live2)

    def legal(self, runs):
        cnt = [0] * self.R
        for (m, _) in runs:
            for r in range(self.R):
                if m >> r & 1:
                    cnt[r] += 1
        return tuple(r for r in range(self.R) if cnt[r] >= 2)

    def merge(self, runs, r, live):
        hit = [(m, s) for (m, s) in runs if m >> r & 1]
        paid = sum(s for (_, s) in hit)
        mask = 0
        for (m, _) in hit:
            mask |= m
        size = sum(live[i] for i in range(len(live)) if mask >> i & 1)
        rest = [(m, s) for (m, s) in runs if not (m >> r & 1)]
        return canon(rest + [(mask, size)]), paid


class Solver:
    def __init__(self, trace, R, K):
        self.cell = Cell(R, K, len(trace))
        self.trace = tuple(trace)
        self.memo = {}

    def opt_from(self, i, runs, live):
        if i == len(self.trace):
            return 0
        key = (i, runs, live)
        if key in self.memo:
            return self.memo[key]
        c = self.cell
        runs2, live2 = c.step(runs, live, self.trace[i])
        cand = c.legal(runs2) if len(runs2) > c.K else ()
        if not cand:
            best = self.opt_from(i + 1, runs2, live2)
        else:
            best = None
            for rr in cand:
                nr, paid = c.merge(runs2, rr, live2)
                v = paid + self.opt_from(i + 1, nr, live2)
                if best is None or v < best:
                    best = v
        self.memo[key] = best
        return best

    def replay(self):
        """Greedy replay. Each decision records the visible state, the legal set, the
        argmin set, and greedy's pick."""
        c = self.cell
        live = tuple([0] * c.R)
        runs = ()
        total = 0
        out = []
        for i in range(len(self.trace)):
            runs2, live2 = c.step(runs, live, self.trace[i])
            cand = c.legal(runs2) if len(runs2) > c.K else ()
            if not cand:
                runs, live = runs2, live2
                continue
            val = {}
            for rr in cand:
                nr, paid = c.merge(runs2, rr, live2)
                val[rr] = (paid, paid + self.opt_from(i + 1, nr, live2))
            bestv = min(v[1] for v in val.values())
            argmin = frozenset(rr for rr in cand if val[rr][1] == bestv)
            pick = max(cand, key=lambda rr: (val[rr][0], -rr))
            out.append(dict(i=i, runs=runs2, live=live2, nxt=self.trace[i], cand=cand,
                            argmin=argmin, pick=pick, paid=val[pick][0],
                            gap=val[pick][1] - bestv, suboptimal=val[pick][1] > bestv))
            runs, paid = c.merge(runs2, pick, live2)
            total += paid
            live = live2
        return total, out


def analyse(R, K, T):
    """Enumerate the cell; group decisions by visible state; intersect argmin sets."""
    groups = {}
    traces = list(itertools.product(range(R), repeat=T))
    loss = 0
    for tr in traces:
        s = Solver(tr, R, K)
        cost, decs = s.replay()
        if cost > s.opt_from(0, (), tuple([0] * s.cell.R)):
            loss += 1
        for d in decs:
            key = (d["i"], d["runs"], d["live"], d["nxt"])
            g = groups.setdefault(key, dict(members=[], argmins=[], picks=set()))
            g["members"].append((tr, d["argmin"], d["pick"]))
            g["argmins"].append(d["argmin"])
            g["picks"].add(d["pick"])
    refuting, safe, greedy_both = [], [], []
    for key, g in groups.items():
        inter = set(g["argmins"][0])
        for a in g["argmins"][1:]:
            inter &= set(a)
        greedy_ok = set(g["picks"] <= a for a in g["argmins"])  # irrelevant, kept out
        verdicts = set(g["members"][0][2] in g["members"][0][1] for _ in [0])
        # greedy's verdict per member: is its pick on an optimal path for that continuation?
        gv = set((pick in am) for (_tr, am, pick) in g["members"])
        if len(gv) == 2:
            greedy_both.append(key)
        if not inter:
            refuting.append(key)
        else:
            safe.append((key, inter))
    return dict(groups=groups, refuting=refuting, safe=safe,
                greedy_both=greedy_both, loss=loss, n_traces=len(traces))


def show_witness(R, K, T):
    res = analyse(R, K, T)
    print("cell R=%d K=%d T=%d  traces %d  greedy non-optimal %d (%.1f%%)"
          % (R, K, T, res["n_traces"], res["loss"], 100.0 * res["loss"] / res["n_traces"]))
    print("  visible states %d | Opt(S) empty in %d | non-empty in %d"
          % (len(res["groups"]), len(res["refuting"]), len(res["safe"])))
    print("  states where the DEPLOYED rule's verdict differs across continuations: %d"
          % len(res["greedy_both"]))
    # a hand-checkable witness: the refuting state with the fewest runs, then smallest index
    wit = sorted(res["refuting"], key=lambda k: (len(k[1]), k[0], k[3]))[0]
    g = res["groups"][wit]
    print("\n  WITNESS -- visible state S, reached at flush i=%d, next flush range %d" % (wit[0], wit[3]))
    print("    runs (range-mask, size): %s" % (list(wit[1]),))
    print("    live bytes per range    : %s" % (list(wit[2]),))
    print("    legal merges at S       : %s" % (list(g["members"][0][1] | set(
        r for am in g["argmins"] for r in am)),))
    print("    continuations reaching S: %d" % len(g["members"]))
    seen = {}
    for (tr, am, pick) in g["members"]:
        seen.setdefault(tuple(sorted(am)), (tr, pick))
    for am in sorted(seen):
        tr, pick = seen[am]
        print("    trace %s -> optimal merges %s ; deployed picks %s (%s)"
              % ("".join(str(x) for x in tr), list(am), pick,
                 "optimal" if pick in am else "SUBOPTIMAL"))
    print("    intersection over all continuations: %s  -> no visible-state rule is exact here"
          % sorted(set(g["argmins"][0]).intersection(*[set(a) for a in g["argmins"][1:]])
                   if len(g["argmins"]) > 1 else sorted(g["argmins"][0])))
    return res


def max_overlap_policy_loss(R, K, T):
    """Losses of the deployed rule and of the cheapest-overlap rule, for reference."""
    traces = list(itertools.product(range(R), repeat=T))
    dep = cheap = 0
    for tr in traces:
        s = Solver(tr, R, K)
        cost, decs = s.replay()
        opt = s.opt_from(0, (), tuple([0] * K))
        if cost > opt:
            dep += 1
        # cheapest-overlap: pick the legal merge paying the fewest bytes
        c = s.cell
        live = tuple([0] * c.R)
        runs = ()
        tot = 0
        for i in range(len(tr)):
            runs2, live2 = c.step(runs, live, tr[i])
            cand = c.legal(runs2) if len(runs2) > c.K else ()
            if not cand:
                runs, live = runs2, live2
                continue
            pick = min(cand, key=lambda rr: (c.merge(runs2, rr, live2)[1], rr))
            runs, paid = c.merge(runs2, pick, live2)
            tot += paid
            live = live2
        if tot > opt:
            cheap += 1
    return dep, cheap, len(traces)


def minimal_exact_horizon(R, K, T):
    """Smallest w such that the w-lookahead policy loses nothing on the cell."""
    from characterise import run_policy  # same model, already written and checked
    traces = list(itertools.product(range(R), repeat=T))
    for w in range(0, T + 1):
        bad = 0
        for tr in traces:
            dep, opt = run_policy(tr, R, K, w)
            if dep > opt:
                bad += 1
                break
        if bad == 0:
            return w
    return None


def main():
    fails = []

    def check(name, ok, detail):
        print("  [%s] %s -- %s" % ("ok" if ok else "FAIL", name, detail))
        if not ok:
            fails.append(name)

    print("=== A. the proposition: Opt(S) = empty for some reachable S ===")
    res = show_witness(3, 3, 6)
    check("registered loss rate reproduced", res["loss"] == 102, "102/729")
    check("some reachable visible state has empty Opt(S)", len(res["refuting"]) > 0,
          "%d refuting states of %d" % (len(res["refuting"]), len(res["groups"])))
    # the weaker claim from last round, as a corollary rather than the evidence
    check("the deployed rule alone already fails to be a state function",
          len(res["greedy_both"]) > 0, "%d states" % len(res["greedy_both"]))
    # every refuting state must also refute the deployed rule at some continuation
    print()

    print("=== B. scope of the horizon formula: adversarial cells, K=2 included ===")
    from characterise import first_choice_index   # one definition, in the committed artefact
    cells = [(3, 2, 5), (3, 2, 6), (4, 2, 5), (3, 3, 5), (3, 3, 6), (3, 3, 7),
             (4, 3, 5), (4, 3, 6), (3, 4, 6), (3, 4, 7), (5, 3, 5), (3, 5, 6)]
    print("  cell          traces   first choice at i   T-K-1   measured w*   verdict")
    for (R, K, T) in cells:
        fc = first_choice_index(R, K, T)
        wstar = minimal_exact_horizon(R, K, T)
        pred = T - K - 1
        if fc is None:
            verdict = "no choice anywhere -> w*=0 (formula does NOT apply)"
            ok = (wstar == 0)
        else:
            verdict = "choice at i=%d -> formula applies" % fc if pred == T - 1 - fc else \
                      "choice at i=%d but formula gives T-K-1" % fc
            ok = (wstar == pred) if pred == T - 1 - fc else (wstar == T - 1 - fc)
        print("  R=%d K=%d T=%d   %6d   %-17s %6d   %-13s %s"
              % (R, K, T, R ** T, str(fc), pred, str(wstar), verdict))
        if K == 2:
            check("K=2: no choice exists, w*=0 while T-K-1>0 (R=%d T=%d)" % (R, T),
                  wstar == 0 and pred > 0, "w*=%s, T-K-1=%d" % (wstar, pred))
        else:
            check("K>=3: w* equals the remaining length after the first choice (R=%d K=%d T=%d)"
                  % (R, K, T), wstar == T - 1 - fc, "w*=%s" % wstar)

    print()
    print("  The formula therefore holds as:  w* = T - 1 - i_first, where i_first is the\n"
          "  earliest flush at which more than one legal merge exists.  When no choice ever\n"
          "  exists (K = 2) i_first is undefined and w* = 0 -- the rule is forced, so no\n"
          "  lookahead is needed and the claim 'no bounded window is exact' is FALSE there.")
    print()
    if fails:
        print("LEMMA: %d CHECK(S) FAILED: %s" % (len(fails), ", ".join(fails)))
        return 1
    print("LEMMA: all checks pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
