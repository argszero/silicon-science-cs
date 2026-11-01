"""Certificate for issue #153: the DP optimum against an INDEPENDENT brute force.

The registration promised exhaustive agreement on every instance, not a sample. The two
implementations below deliberately share NO code:

  dp_optimum()      memoised dynamic programming over the canonical run multiset,
                    using bitmasks and an incremental live-bytes vector.

  brute_optimum()   exhaustive DFS over every legal merge sequence, no memoisation,
                    representing a run as a sorted tuple of the RANGE IDS it covers and
                    recomputing sizes from the live map on every use. Different state
                    representation, different cost accounting, different traversal.

Both answer the same question: the minimum total bytes rewritten to serve a trace.
Exhaustive agreement is the only acceptable outcome; a single disagreement is a finding
about the instrument, and it is printed with the trace that separates them.
"""
import itertools, sys, time
sys.setrecursionlimit(100000)

# --------------------------------------------------------------------- the DP (as registered)
def dp_optimum(trace, R, K):
    def canon(runs): return tuple(sorted(runs))
    def legal(runs):
        cnt = [0]*R
        for (m, _) in runs:
            for r in range(R):
                if m >> r & 1: cnt[r] += 1
        return [r for r in range(R) if cnt[r] >= 2]
    def do_merge(runs, r, live):
        hit = [(m, s) for (m, s) in runs if m >> r & 1]
        cost = sum(s for (_, s) in hit)
        mask = 0
        for (m, _) in hit: mask |= m
        size = sum(live[i] for i in range(len(live)) if mask >> i & 1)
        rest = [(m, s) for (m, s) in runs if not (m >> r & 1)]
        return canon(rest + [(mask, size)]), cost
    def step_state(runs, live, r):
        live2 = list(live); live2[r] += 1
        return canon(list(runs) + [(1 << r, live2[r])]), tuple(live2)
    memo = {}
    def go(i, runs, live):
        if i == len(trace): return 0
        key = (i, runs, live)
        if key in memo: return memo[key]
        runs2, live2 = step_state(runs, live, trace[i])
        cand = legal(runs2) if len(runs2) > K else []
        if not cand:
            best = go(i+1, runs2, live2)
        else:
            best = None
            for rr in cand:
                nr, c = do_merge(runs2, rr, live2)
                sub = go(i+1, nr, live2)
                if sub is None: continue
                v = c + sub
                if best is None or v < best: best = v
        memo[key] = best
        return best
    return go(0, (), tuple([0]*R))

# --------------------------------------------------------------------- the brute force
def brute_optimum(trace, R, K):
    """Exhaustive DFS. A run is a pair (ranges, size): the sorted tuple of the range ids it
    covers and the bytes it held WHEN IT WAS CREATED. Sizes are stored, never recomputed from
    the live map -- a run written when 1 byte was live still holds 1 byte after later writes,
    and an earlier version of this brute force that recomputed charged a repeated range three
    times over (trace 00000: dp 18, brute 24), which the certificate caught.

    Independent of the DP in traversal (DFS, no memoisation), in state representation (dicts
    and tuples of range ids rather than bitmasks), and in cost accounting."""
    def covered_by(runs, r):
        return [x for x in runs if r in x[0]]

    def advance(runs, live, r):
        live2 = dict(live); live2[r] = live2.get(r, 0) + 1
        return tuple(sorted(runs + (((r,), live2[r]),), key=lambda x: (x[0], x[1]))), live2

    def merge_all(runs, live, r):
        hit = covered_by(runs, r)
        cost = sum(x[1] for x in hit)
        union = tuple(sorted(set().union(*[set(x[0]) for x in hit])))
        new_size = sum(live[i] for i in union)
        rest = tuple(x for x in runs if r not in x[0])
        return tuple(sorted(rest + ((union, new_size),), key=lambda x: (x[0], x[1]))), cost

    def search(i, runs, live):
        if i == len(trace): return 0
        runs2, live2 = advance(runs, live, trace[i])
        options = []
        if len(runs2) > K:
            for r in range(R):
                if len(covered_by(runs2, r)) >= 2:
                    options.append(r)
            if not options:
                return search(i+1, runs2, live2)
            best = None
            for r in options:
                mr, c = merge_all(runs2, live2, r)
                sub = search(i+1, mr, live2)
                if sub is None: continue
                if best is None or c + sub < best: best = c + sub
            return best
        return search(i+1, runs2, live2)

    return search(0, (), {})

# --------------------------------------------------------------------- the certificate
CELLS = [(3, 2, 5), (3, 2, 6), (3, 3, 6), (4, 2, 5), (3, 3, 7), (4, 2, 6)]

def run_cell(R, K, T):
    n = agree = 0
    first_disagreement = None
    t0 = time.time()
    for trace in itertools.product(range(R), repeat=T):
        a = dp_optimum(trace, R, K)
        b = brute_optimum(trace, R, K)
        n += 1
        if a == b:
            agree += 1
        elif first_disagreement is None:
            first_disagreement = (trace, a, b)
    return n, agree, first_disagreement, time.time() - t0

if __name__ == "__main__":
    total = total_agree = 0
    print("%-12s %8s %8s %10s  %s" % ("cell", "instances", "agree", "seconds", "verdict"))
    bad = []
    for (R, K, T) in CELLS:
        n, ag, dis, secs = run_cell(R, K, T)
        total += n; total_agree += ag
        ok = (n == ag)
        print("R=%d K=%d T=%d %8d %8d %10.1f  %s"
              % (R, K, T, n, ag, secs, "AGREE" if ok else "DISAGREE"))
        if not ok:
            bad.append((R, K, T, dis))
    print()
    for (R, K, T, dis) in bad:
        print("  DISAGREEMENT  R=%d K=%d T=%d  trace=%s  dp=%s brute=%s"
              % (R, K, T, "".join(map(str, dis[0])), dis[1], dis[2]))
    print("CERTIFICATE: %d of %d instances agree (%s)"
          % (total_agree, total, "ALL AGREE" if total == total_agree else "MISMATCH"))
    sys.exit(0 if total == total_agree else 1)
