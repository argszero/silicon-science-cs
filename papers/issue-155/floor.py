#!/usr/bin/env python3
"""Issue #155 -- the model, the exact floors, and the candidate statistics.

Everything in this file is the instrument the paper's numbers come from. Two
independent methods compute the same optimum, so the fast one (a dynamic
program) is certified against the slow one (exhaustive enumeration) rather than
trusted.

Model
-----
A window of n packets arrives in a known order; packet p carries rank seq[p].
Ranks may repeat. A device has k FIFO queues. An enqueue rule assigns every
packet to exactly one queue; within a queue, arrival order is preserved. Two
dequeue disciplines are compared, and they are NOT interchangeable:

  free merge       the scheduler may emit the head of ANY non-empty queue
                   (the strongest scheduler that could exist -- a lower bound,
                   but no device runs it)
  strict priority  the scheduler emits the head of the lowest-index non-empty
                   queue; the output is Q_0 + Q_1 + ... + Q_{k-1}, each queue in
                   arrival order (what a switch does)

Fidelity metric: rank inversions. Target order is ascending rank. A pair of
equal rank is rank-consistent in either emitted order and is therefore NOT an
inversion -- this is a stated convention of the model, not an artefact of the
implementation, and both methods below count it that way.
"""
import itertools

INF = float("inf")


# --------------------------------------------------------------------------
# statistics under test: each candidate claims to be "the k that is required"
# --------------------------------------------------------------------------

def lds(seq):
    """Longest strictly decreasing subsequence length. The free-merge answer."""
    n = len(seq)
    if not n:
        return 0
    best = [1] * n
    for i in range(n):
        for j in range(i):
            if seq[j] > seq[i] and best[j] + 1 > best[i]:
                best[i] = best[j] + 1
    return max(best)


def inverse_perm(seq):
    """Arrival position of each distinct rank, ranks compressed to 0..m-1."""
    ranks = sorted(set(seq))
    which = {r: i for i, r in enumerate(ranks)}
    p = [0] * len(ranks)
    for pos, rank in enumerate(seq):
        p[which[rank]] = pos
    return p


def runs_of_inverse(seq):
    """runs(p) = 1 + #{i : p[i+1] < p[i]}, p = arrival positions in rank order.

    This is the strict-priority answer for DISTINCT ranks, and a lower bound in
    general (see below).
    """
    p = inverse_perm(seq)
    return 1 + sum(1 for i in range(len(p) - 1) if p[i + 1] < p[i])


def runs_of_order(order):
    """runs of the arrival-position sequence taken in the given packet order."""
    return 1 + sum(1 for i in range(len(order) - 1) if order[i + 1] < order[i])


def order_by_rank(seq, tie_break="stable"):
    sign = 1 if tie_break == "stable" else -1
    return sorted(range(len(seq)), key=lambda p: (seq[p], sign * p))


def stat_t1(seq):
    """runs under a stable tie-break: equal ranks in arrival order."""
    return runs_of_order(order_by_rank(seq, "stable"))


def stat_t2(seq):
    """runs under the anti-stable tie-break: equal ranks in reverse arrival."""
    return runs_of_order(order_by_rank(seq, "reverse"))


def stat_t3(seq):
    """Minimum runs over ALL total orders consistent with non-decreasing rank.

    An algorithm (a minimum over tie-breakings), not a closed form. It reduces
    to runs(p) when ranks are distinct.
    """
    groups = {}
    for p, r in enumerate(seq):
        groups.setdefault(r, []).append(p)
    keys = sorted(groups)
    per = [list(itertools.permutations(groups[k])) for k in keys]
    best = None
    for combo in itertools.product(*per):
        order = []
        for part in combo:
            order.extend(part)
        v = runs_of_order(order)
        if best is None or v < best:
            best = v
    return best


# --------------------------------------------------------------------------
# the floors: cost of an assignment, and the minimum over all assignments
# --------------------------------------------------------------------------

def restricted_output(seq, assign, k):
    """Strict-priority output: queues concatenated in priority order."""
    queues = [[] for _ in range(k)]
    for i, q in enumerate(assign):
        queues[q].append(i)
    out = []
    for q in range(k):
        out.extend(queues[q])
    return out


def count_inversions(seq, out):
    """Pairs whose emitted order disagrees with rank order.

    Equal ranks are skipped: a tie is rank-consistent whichever way it is
    emitted. (An earlier version took the `else` branch for ties and counted
    every tie whose later arrival was emitted first; that is the convention
    defect the certificate in emit_results.py exists to prevent recurring.)
    """
    n = len(seq)
    pos = [0] * n
    for idx, pkt in enumerate(out):
        pos[pkt] = idx
    inv = 0
    for a in range(n):
        for b in range(a + 1, n):
            if seq[a] == seq[b]:
                continue
            hi, lo = (a, b) if seq[a] > seq[b] else (b, a)
            if pos[hi] < pos[lo]:
                inv += 1
    return inv


def restricted_floor_brute(seq, k):
    """Exact minimum cost under strict priority, by enumerating all k^n rules."""
    best = None
    for assign in itertools.product(range(k), repeat=len(seq)):
        c = count_inversions(seq, restricted_output(seq, assign, k))
        if best is None or c < best:
            best = c
    return best


def restricted_floor_dp(seq, k):
    """Exact minimum cost under strict priority, by DP over queue contents.

    The cost of one assignment decomposes over arriving packets: when packet r
    joins queue q, it forms an inversion with every already-queued packet that
    sits in a queue emitted BEFORE q and outranks it, plus every one in a queue
    emitted AFTER q that it outranks. So a state is (arrival index, multiset of
    ranks per queue) and the DP is exact.
    """
    n = len(seq)

    from functools import lru_cache

    @lru_cache(maxsize=None)
    def rec(i, state):
        if i == n:
            return 0
        r = seq[i]
        best = INF
        for q in range(k):
            added = 0
            for qq in range(k):
                block = state[qq]
                if qq <= q:
                    added += sum(1 for x in block if x > r)
                else:
                    added += sum(1 for x in block if x < r)
            nb = list(state)
            # NOTE: extend state[q], never a variable left over from the loop.
            nb[q] = tuple(sorted(state[q] + (r,)))
            cost = added + rec(i + 1, tuple(nb))
            if cost < best:
                best = cost
        return best

    v = rec(0, tuple(() for _ in range(k)))
    rec.cache_clear()
    return v


def free_floor_zero(seq, k):
    """Free merge reaches zero inversions iff the window splits into k
    rank-nondecreasing subsequences, i.e. iff k >= LDS."""
    return lds(seq) <= k


def required_k(seq):
    """The k at which the strict-priority floor first reaches zero."""
    for k in range(1, len(seq) + 1):
        if restricted_floor_dp(seq, k) == 0:
            return k
    return len(seq)


# --------------------------------------------------------------------------
# rules, for the anti-rule control in every measured cell
# --------------------------------------------------------------------------

def band_assign(seq, k, m, aligned=True):
    """Rank-band rule: rank -> contiguous band, band index = queue priority.

    `aligned` puts the lowest ranks in queue 0, which is dequeued first. The
    unaligned variant reverses the priority order and is the control: if it
    cannot lose, the cell measures nothing about ranking and is declined.
    """
    a = [min(k - 1, (r * k) // m) for r in seq]
    return tuple(a if aligned else [k - 1 - x for x in a])


def cost_of_assign(seq, assign, k):
    return count_inversions(seq, restricted_output(seq, assign, k))
