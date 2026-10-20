#!/usr/bin/env python3
"""issue #141 -- v0: the EXACT rank-payoff instrument for evaluation protocols.

Ground truth by construction.  A *strategic evaluation* is declared as

    a GAME (symmetric auctions between n bidders over a finite type grid, declared probabilities)
  x a ZOO   (a declared set of bidding policies; every payoff is an exact sum over the type grid)
  x a PROTOCOL (a score aggregation over a declared opponent population)
  x a POPULATION (weights over the zoo).

Everything below is a Fraction, so every reported quantity is an exact count or an exact expectation:
there is no sampling, no seed and no timing anywhere in this file.

The measured object is the PROTOCOL, through these statistics:

  G (rank-gaming gain)   rank(U*) - rank(pi_rank)   how many positions a policy BUYS by optimizing
                                                    the protocol's score instead of its payoff
  C (payoff cost)        U(U*) - U(pi_rank)         what the bought rank costs in real payoff
  tau (discrimination)   Kendall tau-a of the protocol's ordering against the PAYOFF ordering
  T (transport loss)     fraction of pairwise orderings that change when the population changes

and the theory arm is one-directional and exact:

  a protocol's rank is payoff-monotone (G == 0 in every cell) whenever its score is a strictly
  increasing function of the payoff profile.  The converse is NOT claimed -- it is MEASURED.

The artefact is JSON-native (every exact rational is a string), so the certificate can read the
artefact back and re-derive the headline from the cells it holds: `--out PATH` writes it atomically.

Certificate (--selftest): each item is a two-sided test that carries its OWN plant -- a planted model
which must make THAT item FAIL, because a check whose plant cannot break it is decoration.
  C1 the anchors: each game's equilibrium status is DETERMINED -- a certified restricted symmetric
     equilibrium (exhaustive deviation enumeration; margin exactly 0), or a STATED absence; and for
     fpsb_n2 the analytic closed form b(v) = v/2 is among the certified set.
     PLANT: a zoo whose `eq_fpsb` bids its true value -- the analytic anchor's opposite.
  C2 the zero arm: the monotone reference protocol reads G == 0 and C == 0 in EVERY cell.
     PLANT: a sign-flipped score must move cells.
  C3 the fire arm: at least one non-monotone protocol reads G > 0 somewhere, in every game.
     PLANT: a monotone-only protocol set must make the arm NOT fire.
  C4 the headline RE-DERIVED from the cells equals the reported summary (never the summary compared
     with itself).  PLANT: a corrupted reported max G.
  C5 determinism ACROSS PROCESSES: two runs with independent (randomised) hash seeds emit
     byte-identical JSON, and the byte comparison itself detects a one-byte change; the --json route
     must round-trip (json.loads accepts it) -- the byte leak an exact rational would cause.
"""
import argparse
import copy
import hashlib
import itertools
import json
import os
import subprocess
import sys
from collections import OrderedDict
from fractions import Fraction as F

# ------------------------------------------------------------------------------------------------
# the declared model

NVAL = 8                                          # type grid size
GRID = [F(i, 1) for i in range(1, NVAL + 1)]      # values/signals on {1..8}
P_VAL = F(1, NVAL)
NOISE = [F(e) for e in (-2, -1, 0, 1, 2)]         # the common-value private noise
P_NOISE = F(1, len(NOISE))
BID_LO, BID_HI = F(0), F(NVAL)                    # the declared BID range (a bid is not a value:
                                                  # clamping to the value grid would delete b(1)=1/2)


def shading(c):
    """b(x) = clamp(c * x) onto the bid grid -- the declared zoo's linear family."""
    def f(x):
        return max(BID_LO, min(BID_HI, c * x))
    return f


def const(k):
    return lambda x: F(k)


ZOO = OrderedDict([
    ("eq_fpsb",     shading(F(1, 2))),        # b(v) = v/2 : the 2-bidder FPSB equilibrium shading
    ("eq_spsb",     shading(F(1))),           # b(v) = v   : the SPSB equilibrium (dominant)
    ("shade_3_4",   shading(F(3, 4))),
    ("shade_1_4",   shading(F(1, 4))),
    ("overbid_5_4", shading(F(5, 4))),
    ("bid_min",     const(1)),
    ("bid_mid",     const(4)),
    ("bid_max",     const(8)),
])

# ------------------------------------------------------------------------------------------------
# the games: exact expected payoff of policy `a` against (n-1) copies of policy `b`


def _combs(k):
    """All k-tuples of noise indices (the common-value games' outer enumeration)."""
    out = [()]
    for _ in range(k):
        out = [t + (j,) for t in out for j in range(len(NOISE))]
    return out


def _prob(comb):
    p = F(1)
    for _ in comb:
        p *= P_NOISE
    return p


def _win(ba, opp):
    """1 if the bid beats every opponent bid, an equal split if it ties the top, else 0."""
    top = max(opp)
    if ba > top:
        return F(1)
    if ba == top:
        return F(1, 1 + sum(1 for x in opp if x == top))
    return F(0)


def fpsb(n):
    """First-price sealed bid: the highest bid wins and pays its own bid.  Returns (payoff, win).

    The opponent's bid is a function of the OPPONENT'S OWN value, so their type is enumerated over
    the value grid -- not evaluated at ours.  (The predecessor of this function did the latter, which
    made every private-value payoff degenerate; the certificate caught it: the closed form failed
    and the fire arm never fired.)"""
    others = list(itertools.product(GRID, repeat=n - 1)) if n > 1 else [()]
    def pair(ba, bb):
        pay = win = F(0)
        for v in GRID:
            for ws in others:
                pr = P_VAL * (P_VAL ** (n - 1))
                w = _win(ba(v), [bb(x) for x in ws])
                pay += pr * (v - ba(v)) * w
                win += pr * w
        return pay, win
    return pair


def spsb(n):
    """Second-price sealed bid: the highest bid wins and pays the highest OPPONENT bid.

    `ob` holds the OPPONENTS' bids only, so when our bid wins, the price is `max(ob)` -- the
    second-highest bid OVERALL, since ours is the highest.  (The predecessor of this function
    dropped the top of `ob` and, finding no loser left, fell back to OUR OWN bid -- which silently
    turned every second-price payoff into a FIRST-price one; the tell was `spsb_n2` reporting the
    same certified values as `fpsb_n2`, and the certificate caught it: the weakly dominant
    b(v) = v stopped being a best response, which no second-price auction can do.)"""
    others = list(itertools.product(GRID, repeat=n - 1)) if n > 1 else [()]
    def pair(ba, bb):
        pay = win = F(0)
        for v in GRID:
            for ws in others:
                pr = P_VAL * (P_VAL ** (n - 1))
                ob = [bb(x) for x in ws]
                top = max(ob)
                w = _win(ba(v), ob)
                win += pr * w
                if w > 0:
                    pay += pr * (v - top) * w
        return pay, win
    return pair


def common_value(n):
    """Common value: V uniform on the grid, bidder i sees s_i = V + noise, the winner pays its bid.

    The payoff uses the COMMON V (not the bidder's own signal), which is what makes the winner's
    curse exact rather than rhetorical: the winner is the bidder with the highest signal, so the
    value conditional on winning sits BELOW that signal."""
    def pair(ba, bb):
        pay = win = F(0)
        for V in GRID:
            for ea in range(len(NOISE)):
                sa = V + NOISE[ea]
                if sa not in GRID:
                    continue
                for comb in _combs(n - 1):
                    sb = []
                    for j in comb:
                        sign = V + NOISE[j]
                        if sign not in GRID:
                            break
                        sb.append(sign)
                    else:
                        pr = P_VAL * P_NOISE * _prob(comb)
                        w = _win(ba(sa), [bb(x) for x in sb])
                        pay += pr * (V - ba(sa)) * w
                        win += pr * w
        return pay, win
    return pair


GAMES = OrderedDict([
    ("fpsb_n2", (2, fpsb(2), "first-price, 2 bidders")),
    ("spsb_n2", (2, spsb(2), "second-price, 2 bidders")),
    ("cv_n2",   (2, common_value(2), "common value, 2 bidders")),
    ("cv_n4",   (4, common_value(4), "common value, 4 bidders")),
])


def matrices(game):
    """(payoff matrix, OUTCOME matrix) -- both exact.  The outcome matrix is who WINS the game; the
    payoff matrix is who PROFITS from it, and the two are different objects by construction."""
    _, f, _ = GAMES[game]
    M = OrderedDict()
    W = OrderedDict()
    for a in ZOO:
        M[a] = OrderedDict()
        W[a] = OrderedDict()
        for b in ZOO:
            M[a][b], W[a][b] = f(ZOO[a], ZOO[b])
    return M, W


# ------------------------------------------------------------------------------------------------
# populations and protocols

def populations():
    """Declared opponent populations (weights over the zoo).  Each is a distribution: sum == 1."""
    z = list(ZOO)
    uni = OrderedDict((a, F(1, len(z))) for a in z)

    def skew(names):
        d = OrderedDict()
        denom = len(z) + len(names)
        for a in z:
            d[a] = F(2, denom) if a in names else F(1, denom)
        return d

    def capped(keep):
        return OrderedDict((a, (F(1, len(keep)) if a in keep else F(0))) for a in z)

    return OrderedDict([
        ("uniform", uni),
        ("strong_skew", skew(["eq_fpsb", "eq_spsb", "shade_3_4"])),
        ("weak_skew", skew(["shade_1_4", "bid_min", "bid_mid"])),
        ("capped_strong", capped(["eq_fpsb", "eq_spsb", "overbid_5_4", "bid_max"])),
    ])


def _mean(M, a, pop):
    return sum((M[a][b] * w for b, w in pop.items()), F(0))


def _beats(M, a, b):
    return F(1) if M[a][b] > M[b][a] else (F(1, 2) if M[a][b] == M[b][a] else F(0))


PROTOCOLS = OrderedDict([
    # -- monotone in the payoff profile: the ZERO arm of the two-sided test
    ("mean_payoff",   lambda M, a, pop, W: _mean(M, a, pop)),
    # -- the OUTCOME score: who WINS the game, ignoring what the win costs.  This is the channel a
    #    real leaderboard usually publishes, and its divergence from profit is the paper's subject.
    ("game_wins",     lambda M, a, pop, W: sum((w * W[a][b] for b, w in pop.items()), F(0))),
    # -- signs only, read off the PAYOFF comparison (a win count / Elo single round-robin is an
    #    AFFINE transform of this, so it is one protocol and not two)
    ("win_count",     lambda M, a, pop, W: sum((w * _beats(M, a, b) for b, w in pop.items()), F(0))),
    # -- ordinal and TIE-FREE: only a strict payoff win counts, a tie earns nothing
    ("strict_wins",   lambda M, a, pop, W: sum(
        (w * (F(1) if M[a][b] > M[b][a] else F(0)) for b, w in pop.items()), F(0))),
    # -- each opponent normalised by the best achievable against it: keeps ratios, discards level
    ("norm_by_best",  lambda M, a, pop, W: sum(
        (w * (M[a][b] / max(M[x][b] for x in ZOO) if max(M[x][b] for x in ZOO) != 0 else F(0))
         for b, w in pop.items()), F(0))),
    # -- the pair's own spread: local normalisation by the two policies' own numbers
    ("relative_pair", lambda M, a, pop, W: sum(
        (w * ((M[a][b] - M[b][a]) / (abs(M[a][b]) + abs(M[b][a]) + F(1, 1000)))
         for b, w in pop.items()), F(0))),
    # -- champion: only an outright best-in-population counts, everything else is 0
    ("champion",      lambda M, a, pop, W: sum(
        (w * (F(1) if all(M[a][x] > M[x][a] for x in ZOO if pop[x] > 0 and x != a) else F(0))
         for b, w in pop.items()), F(0))),
])

# ------------------------------------------------------------------------------------------------
# rankings and the statistics


def order_by(scores):
    """A total order: descending score, ties broken lexicographically (stated convention)."""
    return sorted(scores, key=lambda a: (-scores[a], a))


def ranks_of(scores):
    return {a: i + 1 for i, a in enumerate(order_by(scores))}


def payoff_order(M, pop):
    return order_by(OrderedDict((a, _mean(M, a, pop)) for a in ZOO))


def tie_pairs(scores):
    """How many unordered pairs are TIED -- the tie convention is a coordinate, so it is reported."""
    names = list(scores)
    return sum(1 for i, a in enumerate(names) for b in names[i + 1:] if scores[a] == scores[b])


def kendall_tau_a(o1, o2):
    """(tau-a, discordant, total) between two orderings of the same set."""
    pos = {a: i for i, a in enumerate(o2)}
    dis = con = 0
    for i, a in enumerate(o1):
        for b in o1[i + 1:]:
            if pos[a] < pos[b]:
                con += 1
            else:
                dis += 1
    tot = con + dis
    return (F(con - dis, tot) if tot else F(0)), dis, tot


def cell(M, pop, protocol_fn, W):
    """One (game, population, protocol) cell: scores, orderings, G, C, tau."""
    scores = OrderedDict((a, protocol_fn(M, a, pop, W)) for a in ZOO)
    u = OrderedDict((a, _mean(M, a, pop)) for a in ZOO)
    r_pay = ranks_of(u)
    r_scr = ranks_of(scores)
    pi_money = min(u, key=lambda a: (r_pay[a], a))       # the payoff-optimal policy
    pi_rank = min(scores, key=lambda a: (r_scr[a], a))   # the score-optimal policy
    tau, dis, tot = kendall_tau_a(order_by(scores), order_by(u))
    return {
        "pi_money": pi_money,
        "pi_rank": pi_rank,
        "rank_money_in_scores": r_scr[pi_money],
        "rank_bought": r_scr[pi_rank],
        # how many positions the PROTOCOL puts between the policy it leads with and the policy that
        # actually pays best -- both ranks read in the protocol's own ranking (one coordinate system)
        "G": r_scr[pi_money] - r_scr[pi_rank],
        # every exact rational leaves this function as a STRING, so the artefact is JSON-native and
        # the certificate parses the value back out of the artefact rather than trusting a float
        "C": str(u[pi_money] - u[pi_rank]),
        "U_money": str(u[pi_money]),
        "U_bought": str(u[pi_rank]),
        "tau": str(tau),
        "discordant": dis,
        "pairs": tot,
        "ties": tie_pairs(scores),
        "scores": OrderedDict((a, str(scores[a])) for a in ZOO),
    }


# ------------------------------------------------------------------------------------------------
# the anchors: a restricted symmetric equilibrium, proved by exhaustive deviation enumeration

def equilibria(M):
    """Every zoo member that is a best response to a population concentrated on ITSELF.

    This is the restricted symmetric equilibrium, found by ENUMERATING candidates and certifying
    each by exhaustive deviation enumeration -- never by best-response iteration, which can cycle
    (measured: it does, for `spsb_n2` and `cv_n4`, and this function's predecessor then reported the
    non-equilibrium it stopped on as if it were one).  A set with no member is a finding: the
    declared zoo carries no restricted symmetric equilibrium."""
    out = []
    for cand in ZOO:
        pop = OrderedDict((a, (F(1) if a == cand else F(0))) for a in ZOO)
        val = _mean(M, cand, pop)
        best = max((_mean(M, a, pop), a) for a in ZOO)
        margin = best[0] - val
        if margin == 0:
            out.append({"policy": cand, "value": str(val), "margin": "0",
                        "best_response": cand})
        else:
            out.append({"policy": cand, "value": str(val), "margin": str(margin),
                        "best_response": best[1], "certified": False})
    return [e for e in out if "certified" not in e] or [], out


def closed_form_check(game, eq_policy):
    """The FPSB anchor: b(v) = v/2 must be exactly the zoo's winning policy AND the shading v/2."""
    if game != "fpsb_n2":
        return None
    f = ZOO[eq_policy]
    return all(f(v) == v / 2 for v in GRID)


def dominant_check(policy, zoo=None):
    """The SPSB anchor: a second-price auction's weakly dominant strategy is b(v) = v on the grid."""
    zoo = ZOO if zoo is None else zoo
    f = zoo[policy]
    return all(f(v) == v for v in GRID)


# ------------------------------------------------------------------------------------------------
# the study

def run():
    pops = populations()
    cells = OrderedDict()
    eqs = OrderedDict()
    transport = OrderedDict()

    for g in GAMES:
        M, W = matrices(g)
        es, allc = equilibria(M)
        eqs[g] = {"policies": [e["policy"] for e in es], "count": len(es),
                  "values": [e["value"] for e in es],
                  "no_restricted_equilibrium": not es,
                  "equilibrium_reason": (None if es else
                      "no zoo member is a best response to a population concentrated on itself: "
                      "every candidate has a profitable linear deviation, so the best responses "
                      "cycle out of the declared (linear-shading) zoo -- the winner's-curse regime "
                      "needs a richer zoo, and that is a finding about the zoo, not about the game"),
                  "margins": OrderedDict((e["policy"], e["margin"]) for e in allc),
                  # the closed form is a MEMBER of the certified set, not the whole of it: on a
                  # discrete grid a restricted zoo can carry several best responses
                  "closed_form_v_over_2": any(closed_form_check(g, e["policy"]) for e in es)}
        for pname, pop in pops.items():
            for prname, fn in PROTOCOLS.items():
                cells["%s|%s|%s" % (g, pname, prname)] = cell(M, pop, fn, W)
        # transport: the SAME protocol's ordering under two populations
        for prname, fn in PROTOCOLS.items():
            for p1, p2 in (("uniform", "strong_skew"), ("uniform", "weak_skew"),
                           ("uniform", "capped_strong")):
                o1 = order_by(OrderedDict((a, fn(M, a, pops[p1], W)) for a in ZOO))
                o2 = order_by(OrderedDict((a, fn(M, a, pops[p2], W)) for a in ZOO))
                tau, dis, tot = kendall_tau_a(o1, o2)
                transport["%s|%s|%s>%s" % (g, prname, p1, p2)] = {
                    "tau": str(tau), "discordant": dis, "pairs": tot,
                    "loss": str(F(dis, tot) if tot else F(0))}

    findings = OrderedDict()
    zero_arm = [k for k, c in cells.items()
                if k.split("|")[2] == "mean_payoff" and (c["G"] != 0 or F(c["C"]) != 0)]
    findings["zero_arm_violations"] = len(zero_arm)
    findings["cells"] = len(cells)
    per_proto = OrderedDict()
    for prname in PROTOCOLS:
        sub = [c for k, c in cells.items() if k.split("|")[2] == prname]
        per_proto[prname] = {
            "cells": len(sub),
            "G_pos": sum(1 for c in sub if c["G"] > 0),
            "G_max": str(max(c["G"] for c in sub)),
            "G_mean": str(sum((c["G"] for c in sub), F(0)) / len(sub)),
            "C_max": str(max(F(c["C"]) for c in sub)),
            "tau_mean": str(sum((F(c["tau"]) for c in sub), F(0)) / len(sub)),
        }
    findings["per_protocol"] = per_proto
    findings["transport_mean"] = OrderedDict(
        (p, str(sum((F(t["loss"]) for k, t in transport.items() if k.split("|")[1] == p), F(0))
                / max(1, sum(1 for k in transport if k.split("|")[1] == p))))
        for p in PROTOCOLS)
    per_game_pos = OrderedDict()
    for g in GAMES:
        sub = [c for k, c in cells.items() if k.startswith(g + "|")]
        per_game_pos[g] = sum(1 for c in sub if c["G"] > 0)
    findings["G_pos_per_game"] = per_game_pos
    return {"games": OrderedDict((g, GAMES[g][2]) for g in GAMES),
            "zoo": list(ZOO), "protocols": list(PROTOCOLS),
            "populations": list(populations()),
            "equilibria": eqs, "cells": cells, "transport": transport, "findings": findings}


def dump(doc, path=None):
    txt = json.dumps(doc, indent=1, sort_keys=True) + "\n"
    if path:
        tmp = path + ".stage"
        with open(tmp, "w", encoding="utf-8") as fh:
            fh.write(txt)
        os.replace(tmp, path)
    return txt


# ------------------------------------------------------------------------------------------------
# the certificate

def _run_planted(zoo=None, protocols=None):
    """Run the study against a PLANTED model -- the object a certificate item must reject if broken."""
    global ZOO, PROTOCOLS
    keep_zoo, keep_prot = ZOO, PROTOCOLS
    try:
        if zoo is not None:
            ZOO = zoo
        if protocols is not None:
            PROTOCOLS = protocols
        return run()
    finally:
        ZOO, PROTOCOLS = keep_zoo, keep_prot


def _rederive_headline(doc):
    """(max G, #cells with G > 0) re-derived from the CELLS the artefact carries."""
    return (max(c["G"] for c in doc["cells"].values()),
            sum(1 for c in doc["cells"].values() if c["G"] > 0))


def _reported_headline(doc):
    """The same two numbers as the artefact REPORTS them in its summary block."""
    per = doc["findings"]["per_protocol"]
    return (max(F(v["G_max"]) for v in per.values()), sum(v["G_pos"] for v in per.values()))


def _subprocess_json():
    """One --json run in a FRESH process with an independent (randomised) hash seed."""
    env = dict(os.environ)
    env.pop("PYTHONHASHSEED", None)
    r = subprocess.run([sys.executable, os.path.abspath(__file__), "--json"],
                       capture_output=True, text=True, check=True, env=env)
    return r.stdout


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def selftest():
    ok = total = 0

    def check(name, cond, detail=""):
        nonlocal ok, total
        total += 1
        if cond:
            ok += 1
            print("  OK   %s%s" % (name, ("  [%s]" % detail) if detail else ""))
        else:
            print("  FAIL %s%s" % (name, ("  [%s]" % detail) if detail else ""))

    doc = run()

    print("C1 -- the anchors: a certified restricted equilibrium, or a stated absence")
    for g in GAMES:
        e = doc["equilibria"][g]
        check("%s: equilibrium status is DETERMINED (certified set, or a stated absence)" % g,
              e["count"] >= 1 or (e["no_restricted_equilibrium"] and e["equilibrium_reason"]),
              "policies=%s" % (e["policies"] or "NONE (recorded with its reason)"))
    check("fpsb_n2's closed form b(v) = v/2 is AMONG the certified equilibria",
          doc["equilibria"]["fpsb_n2"]["closed_form_v_over_2"] is True)
    check("spsb_n2: the weakly dominant b(v) = v is the identity AND is certified",
          dominant_check("eq_spsb") and "eq_spsb" in doc["equilibria"]["spsb_n2"]["policies"],
          "identity=%s certified=%s" % (dominant_check("eq_spsb"),
                                        doc["equilibria"]["spsb_n2"]["policies"]))
    check("cv_n4's absence is recorded as a finding AND is not shared by cv_n2",
          doc["equilibria"]["cv_n4"]["no_restricted_equilibrium"] is True
          and doc["equilibria"]["cv_n2"]["no_restricted_equilibrium"] is False)
    bad_zoo = OrderedDict(ZOO)
    bad_zoo["eq_fpsb"] = shading(F(1))          # bid your true value -- the analytic anchor's opposite
    pd = _run_planted(zoo=bad_zoo)
    check("a PLANTED non-equilibrium ZOO breaks the FPSB anchor (C1 is a test, not a print)",
          pd["equilibria"]["fpsb_n2"]["closed_form_v_over_2"] is False,
          "planted eq_fpsb=shading(1) -> closed-form-among-certified=%s"
          % pd["equilibria"]["fpsb_n2"]["closed_form_v_over_2"])
    dom_zoo = OrderedDict(ZOO)
    dom_zoo["eq_spsb"] = shading(F(1, 2))       # the zoo no longer carries a dominant strategy
    pd = _run_planted(zoo=dom_zoo)
    check("a PLANTED zoo without the dominant strategy breaks the SPSB anchor (C1 is a test)",
          not (dominant_check("eq_spsb", dom_zoo)
               and "eq_spsb" in pd["equilibria"]["spsb_n2"]["policies"]))

    print("C2 -- the ZERO arm: the monotone reference reads G == 0 and C == 0 in every cell")
    zero = [k for k, c in doc["cells"].items()
            if k.split("|")[2] == "mean_payoff" and (c["G"] != 0 or F(c["C"]) != 0)]
    check("mean_payoff: %d cells, 0 with G != 0 or C != 0" % len(doc["cells"]), not zero,
          ", ".join(zero[:3]))
    perverse = OrderedDict([("mean_payoff", lambda M, a, pop, W: -_mean(M, a, pop))]
                           + [(k, f) for k, f in PROTOCOLS.items() if k != "mean_payoff"])
    pd = _run_planted(protocols=perverse)
    moved = [k for k, c in pd["cells"].items() if c["G"] != 0 or F(c["C"]) != 0]
    check("a PLANTED perverse score IS caught (the zero arm is a test)", bool(moved),
          "%d/%d cells move" % (len(moved), len(pd["cells"])))

    print("C3 -- the FIRE arm: a non-monotone protocol reads G > 0 somewhere, in every game")
    for g in GAMES:
        n = doc["findings"]["G_pos_per_game"][g]
        check("%s: a non-monotone protocol buys rank in at least one cell" % g, n > 0,
              "%d cells with G > 0" % n)
    mono_only = OrderedDict([("mean_payoff", PROTOCOLS["mean_payoff"])])
    pd = _run_planted(protocols=mono_only)
    check("a PLANTED monotone-only protocol set makes the fire arm NOT fire (C3 is a test)",
          all(n == 0 for n in pd["findings"]["G_pos_per_game"].values()),
          "G>0 per game: %s" % dict(pd["findings"]["G_pos_per_game"]))

    print("C4 -- the headline is RE-DERIVED from the cells, not compared with itself")
    check("the reported (max G, #cells with G>0) equals the re-derivation",
          _reported_headline(doc) == _rederive_headline(doc),
          "reported=%s re-derived=%s" % (_reported_headline(doc), _rederive_headline(doc)))
    tam = copy.deepcopy(doc)
    tam["findings"]["per_protocol"]["mean_payoff"]["G_max"] = "99"
    check("a PLANTED wrong reported max G is caught (C4 is a test, not a print)",
          _reported_headline(tam) != _rederive_headline(tam),
          "planted report=%s" % (_reported_headline(tam),))
    # the artefact is the CLAIM: write it, read it BACK FROM DISK, re-derive the headline from ITS cells
    staging = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".selftest-artefact.json")
    try:
        dump(doc, staging)
        with open(staging, encoding="utf-8") as fh:
            back = json.load(fh)
    finally:
        if os.path.exists(staging):
            os.remove(staging)
    check("the artefact read back FROM DISK carries the cells its headline is re-derived from",
          _rederive_headline(back) == _reported_headline(back) == _rederive_headline(doc),
          "disk re-derivation=%s" % (_rederive_headline(back),))

    print("C5 -- determinism ACROSS PROCESSES, and the comparison itself is a test")
    p1 = _subprocess_json()
    p2 = _subprocess_json()
    check("two PROCESSES with randomised hash seeds emit byte-identical JSON", p1 == p2,
          "%d bytes" % len(p1))
    corrupted = p1[:-2] + ("Z" if p1[-2] != "Z" else "Q") + p1[-1]
    check("the byte comparison DETECTS a one-byte change (the determinism check is a test)",
          p1 != corrupted)
    check("the --json route round-trips (no exact rational leaked into the artefact)",
          isinstance(json.loads(p1), dict) and json.loads(p1)["findings"]["cells"] == len(doc["cells"]))

    check("every population is a distribution (weights sum to 1)",
          all(sum(p.values(), F(0)) == 1 for p in populations().values()))

    print("SELFTEST %d/%d" % (ok, total))
    return 0 if ok == total else 1


# ------------------------------------------------------------------------------------------------
# the report

def report_text(doc):
    L = ["== issue #141 -- v0: the exact rank-payoff instrument ==",
         "   %d games x %d policies x %d populations x %d protocols = %d cells; all values exact"
         % (len(GAMES), len(ZOO), len(doc["populations"]), len(doc["protocols"]),
            len(doc["cells"])),
         "",
         "== THE ANCHORS (restricted symmetric equilibrium, certified by deviation enumeration) =="]
    for g, e in doc["equilibria"].items():
        L.append("   %-9s %-24s certified: %-26s value(s)=%-18s closed-form v/2 among them: %s"
                 % (g, doc["games"][g], ",".join(e["policies"]) or "(NONE -- stated as a finding)",
                    ",".join(e["values"]) or "-", e["closed_form_v_over_2"]))
    L += ["", "== PER PROTOCOL (over all games and populations) ==",
          "   %-14s %5s %6s %8s %10s %12s %10s"
          % ("protocol", "cells", "G>0", "max G", "mean G", "max cost C", "mean tau")]
    for p, v in doc["findings"]["per_protocol"].items():
        L.append("   %-14s %5d %6d %8s %10s %12.5s %10s"
                 % (p, v["cells"], v["G_pos"], v["G_max"], v["G_mean"], F(v["C_max"]).__float__(),
                    F(v["tau_mean"]).__float__()))
    L += ["", "== TRANSPORT LOSS (share of pairwise orderings that change with the population) =="]
    for p, v in doc["findings"]["transport_mean"].items():
        L.append("   %-14s mean loss = %s" % (p, v))
    L += ["", "== WHERE THE GAIN IS (cells with G > 0 per game) =="]
    per_game = len(doc["populations"]) * len(doc["protocols"])
    for g, n in doc["findings"]["G_pos_per_game"].items():
        L.append("   %-9s %d of %d cells" % (g, n, per_game))
    L += ["", "== THE CELLS THAT BUY THE MOST RANK (top 8 by G) ==",
          "   %-9s %-14s %-14s %3s %-10s %-10s %10s"
          % ("game", "population", "protocol", "G", "payoff-opt", "rank-opt", "cost C")]
    for k, c in sorted(doc["cells"].items(), key=lambda kv: (-kv[1]["G"], kv[0]))[:8]:
        g, p, pr = k.split("|")
        L.append("   %-9s %-14s %-14s %3d %-10s %-10s %10s"
                 % (g, p, pr, c["G"], c["pi_money"], c["pi_rank"],
                    ("%.6f" % F(c["C"]).__float__())))
    L += ["", "== THE ZERO ARM (the monotone reference) ==",
          "   cells with G != 0 or C != 0: %d  (of %d)"
          % (doc["findings"]["zero_arm_violations"], doc["findings"]["cells"]), ""]
    return "\n".join(L)


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--text", action="store_true")
    ap.add_argument("--out", metavar="PATH", help="write the JSON artefact atomically to PATH")
    a = ap.parse_args(argv[1:])
    if a.selftest:
        return selftest()
    doc = run()
    if a.out:
        dump(doc, a.out)
        sys.stdout.write("wrote %s  bytes=%d  sha256=%s\n"
                         % (a.out, os.path.getsize(a.out), sha256_file(a.out)))
        return 0
    if a.json:
        sys.stdout.write(dump(doc))
        return 0
    sys.stdout.write(report_text(doc))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
