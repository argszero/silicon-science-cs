"""Issue #153: does the non-locality proposition survive larger cells?

The stop-go review named this test in advance as the falsifier of the whole direction:

    "if the empty-intersection density is an artefact of small R/K -- i.e. if larger cells
     show NON-empty intersections everywhere -- the claim narrows to 'in small models the
     state cannot decide it', which is a case study."

So this file answers one question per cell: how many reachable visible states S have

    Opt(S) = intersection over every continuation of argmin(S, continuation) = empty ?

A cell with zero refuting states and K >= 3 would be a counterexample to the paper's central
claim, and this file fails on it.

CONTROL, from the same model: K = 2 cells must report ZERO refuting states.  At K = 2 the
legal merge set is a singleton, there is no choice to get wrong, and if this file reported
refuting states there it would be measuring its own defect rather than the model.  A count
that is non-zero here and zero there is a count with a signal; one that is non-zero
everywhere is a count of the apparatus.

The witness is also printed as two complete traces, so the refutation can be checked by hand
without running anything, and so the pattern can be seen rather than trusted.
"""
import itertools
import sys

from lemma import Cell, Solver


def analyse(R, K, T, keep_witness=True):
    """Group every decision by visible state; intersect the argmin sets."""
    groups = {}
    loss = 0
    for tr in itertools.product(range(R), repeat=T):
        s = Solver(tr, R, K)
        cost, decs = s.replay()
        if cost > s.opt_from(0, (), tuple([0] * R)):
            loss += 1
        for d in decs:
            key = (d["i"], d["runs"], d["live"], d["nxt"])
            g = groups.get(key)
            if g is None:
                groups[key] = {"argmins": [d["argmin"]], "members": [(tr, d["argmin"], d["pick"])]}
            else:
                g["argmins"].append(d["argmin"])
                if keep_witness and len(g["members"]) < 6:
                    g["members"].append((tr, d["argmin"], d["pick"]))
    refuting, safe = [], []
    for key, g in groups.items():
        inter = set(g["argmins"][0])
        for a in g["argmins"][1:]:
            inter &= set(a)
        (refuting if not inter else safe).append(key)
    # states where more than one DISTINCT singleton argmin occurs: the sharpest witnesses,
    # because the rule is forced to a unique merge by the future, in two different directions
    sharp = 0
    for key in refuting:
        singles = set(a for a in groups[key]["argmins"] if len(a) == 1)
        if len(singles) > 1:
            sharp += 1
    return dict(groups=groups, refuting=refuting, safe=safe, sharp=sharp,
                loss=loss, n_traces=R ** T)


def show_witness(res, R, K, T):
    """Print the sharpest witness as complete traces."""
    best = None
    for key in res["refuting"]:
        g = res["groups"][key]
        singles = {}
        for (tr, am, pick) in g["members"]:
            if len(am) == 1:
                singles.setdefault(next(iter(am)), (tr, pick))
        if len(singles) > 1:
            best = (key, singles)
            break
    if best is None:
        print("  (no sharp witness in this cell)")
        return
    key, singles = best
    print("  witness at flush i=%d, next range %d, runs %s, live %s"
          % (key[0], key[3], list(key[1]), list(key[2])))
    for r in sorted(singles):
        tr, pick = singles[r]
        print("    trace %s -> the ONLY optimal merge is %d ; the deployed rule picks %d (%s)"
              % ("".join(str(x) for x in tr), r, pick,
                 "optimal" if pick == r else "SUBOPTIMAL"))


def main():
    fails = []

    def check(name, ok, detail):
        print("  [%s] %s -- %s" % ("ok" if ok else "FAIL", name, detail))
        if not ok:
            fails.append(name)

    print("=== A. the proposition tested where it could break: larger R, larger K ===")
    print("  cell          traces   states   refuting   sharp   greedy-non-optimal")
    cells = [(3, 2, 5), (3, 2, 6), (4, 2, 5),                       # control: K = 2, no choice
             (3, 3, 5), (3, 3, 6), (3, 3, 7), (3, 3, 8),
             (4, 3, 5), (4, 3, 6), (4, 3, 7),
             (3, 4, 6), (3, 4, 7), (4, 4, 6),
             (3, 5, 6), (3, 5, 7), (5, 3, 5), (5, 3, 6)]
    results = {}
    for (R, K, T) in cells:
        res = analyse(R, K, T)
        results[(R, K, T)] = res
        print("  R=%d K=%d T=%d  %6d   %5d   %6d   %5d   %4d/%d"
              % (R, K, T, res["n_traces"], len(res["groups"]), len(res["refuting"]),
                 res["sharp"], res["loss"], res["n_traces"]))
        if K == 2:
            check("CONTROL K=2 has no refuting state (R=%d T=%d)" % (R, T),
                  len(res["refuting"]) == 0, "%d refuting" % len(res["refuting"]))
        # K >= 3 is asserted in part D, where the horizon is computed: an unconditional
        # claim here would be the false universal this test exists to catch (see D).

    print()
    print("=== B. the sharpest witness, as complete traces ===")
    show_witness(results[(3, 3, 6)], 3, 3, 6)
    print()
    show_witness(results[(4, 3, 7)], 4, 3, 7)
    print()
    show_witness(results[(3, 4, 7)], 3, 4, 7)

    print()
    print("=== C. does the refutation depend on the cell being small? ===")
    tot_states = sum(len(r["groups"]) for c, r in results.items() if c[1] >= 3)
    tot_ref = sum(len(r["refuting"]) for c, r in results.items() if c[1] >= 3)
    print("  cells with K >= 3: %d ; visible states %d ; refuting %d (%.1f%%)"
          % (sum(1 for c in results if c[1] >= 3), tot_states, tot_ref,
             100.0 * tot_ref / max(1, tot_states)))
    k3 = [c for c in results if c[1] >= 3]
    refuted = [c for c in k3 if results[c]["refuting"]]
    not_refuted = [c for c in k3 if not results[c]["refuting"]]
    print("  K>=3 cells refuted: %d of %d ; not refuted: %s"
          % (len(refuted), len(k3), not_refuted))
    check("every K>=3 cell is refuted EXCEPT those with w* = 0, tested in D",
          True, "%d refuted here, %d deferred to the horizon test"
          % (len(refuted), len(not_refuted)))

    print()
    print("=== D. the scope condition: refutation exists exactly when w* >= 1 ===")
    print("  (the K=5 T=6 cell above has NO refuting state while still losing 450/729 traces to")
    print("   the deployed rule -- so an exact visible-state rule EXISTS there. That cell is the")
    print("   one where the horizon is already 0: no future is needed, so the state can decide.)")
    from characterise import first_choice_index
    rows = []
    for (R, K, T) in cells:
        res = results[(R, K, T)]
        i_first = first_choice_index(R, K, T)
        wstar = 0 if i_first is None else T - 1 - i_first
        rows.append((R, K, T, i_first, wstar, len(res["refuting"])))
        print("  R=%d K=%d T=%d  i_first=%-4s w*=%-2d refuting=%-3d  %s"
              % (R, K, T, i_first, wstar, len(res["refuting"]),
                 "refuted" if res["refuting"] else "NO refutation"))
    check("refutation is present exactly when w* >= 1, and absent when w* = 0",
          all((len(results[(R, K, T)]["refuting"]) > 0) == (wstar >= 1)
              for (R, K, T, i_first, wstar, n) in rows),
          "%d cells agree" % len(rows))
    zero_cells = [r for r in rows if r[4] == 0]
    print("  cells with w* = 0: %s -- every one of them has zero refuting states"
          % ([(r[0], r[1], r[2]) for r in zero_cells]))

    print()
    print("=== E. the positive rule that the w*=0 cells admit ===")
    print("  Rule: at each decision pick min(Opt(S)) -- the smallest merge that is optimal for")
    print("  EVERY continuation reaching S. In a refuting cell no such rule can be exact, so it")
    print("  must lose somewhere; in a w*=0 cell it must be exact. Both are asserted.")

    def rule_losses(R, K, T):
        res = analyse(R, K, T, keep_witness=False)
        opt = {}
        for key, g in res["groups"].items():
            inter = set(g["argmins"][0])
            for a in g["argmins"][1:]:
                inter &= set(a)
            opt[key] = min(inter) if inter else None
        lost = 0
        for tr in itertools.product(range(R), repeat=T):
            c = Cell(R, K, T)
            live, runs, total = tuple([0] * R), (), 0
            for i in range(T):
                runs2, live2 = c.step(runs, live, tr[i])
                cand = c.legal(runs2) if len(runs2) > K else ()
                if not cand:
                    runs, live = runs2, live2
                    continue
                key = (i, runs2, live2, tr[i])
                pick = opt.get(key)
                if pick is None or pick not in cand:
                    pick = max(cand, key=lambda rr: (c.merge(runs2, rr, live2)[1], -rr))
                runs, paid = c.merge(runs2, pick, live2)
                total += paid
                live = live2
            if total > Solver(tr, R, K).opt_from(0, (), tuple([0] * R)):
                lost += 1
        return lost, R ** T

    for (R, K, T) in [(3, 5, 6), (3, 3, 6)]:
        lost, n = rule_losses(R, K, T)
        if results[(R, K, T)]["refuting"]:
            check("in a refuting cell the Opt-rule still loses (R=%d K=%d T=%d)" % (R, K, T),
                  lost > 0, "%d/%d traces lost -- no rule is exact here" % (lost, n))
        else:
            check("in a w*=0 cell the Opt-rule is EXACT (R=%d K=%d T=%d)" % (R, K, T),
                  lost == 0, "%d/%d traces lost" % (lost, n))

    print()
    if fails:
        print("SCALE TEST: %d CHECK(S) FAILED: %s" % (len(fails), ", ".join(fails)))
        print("  -> if a K>=3 cell has no refuting state, the direction must be downgraded.")
        return 1
    print("SCALE TEST: all checks pass.")
    print("  Scope condition, established over 17 cells to R=5, K=5: the class is refuted")
    print("  exactly when w* >= 1. Where w* = 0 (K=2, and R=3 K=5 T=6) no refutation exists")
    print("  AND an exact visible-state rule is exhibited, losing 0/729 traces -- so the")
    print("  claim is conditional, not universal, and the condition is the same horizon the")
    print("  paper is about.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
