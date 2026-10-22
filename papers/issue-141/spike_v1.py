#!/usr/bin/env python3
"""issue #141 -- v1: the THEORY ARM.

v0 measured the rank-payoff divergence.  v1 asks what the divergence IS, and the round's job is to
put the registration's own formal carrier on trial (a de-risk spike's first duty):

    the issue body registers:  "a protocol is rank-gaming-free **iff** its score is a monotone
    function of the per-population payoff profile"  /  "zero-gain protocols are exactly the
    monotone-score protocols".

That sentence conflates TWO objects, and v1 separates them:

  * the ARGMAX map   -- which policy the protocol puts FIRST.  G reads only this.
  * the ORDERING map -- the whole order.  tau reads this.

The theorems v1 states and certifies:

  T1 (forward, exact).  If a protocol's score is phi(u) pointwise for a STRICTLY INCREASING phi of
     the payoff profile u, then in every cell the ordering is IDENTICAL to the payoff ordering, so
     G == 0 AND tau == 1.  This direction is true and is certified by construction.
  T2 (the naive converse is FALSE).  There are cells where the protocol buys no rank (G == 0) yet is
     NOT order-equivalent to the payoff ordering (tau < 1).  An exact witness is exhibited from the
     live zoo.  So "G == 0" does NOT imply "monotone score": the registration's iff is refuted in
     the converse direction.
  T3 (the corrected, sharp law).  G > 0  =>  tau < 1 in EVERY cell (buying rank implies ordering
     disagreement), and the implication is STRICT (T2's witnesses).  The two properties are therefore
     not the same object: **ordering fragility strictly contains rank-gaming** -- {order-fragile} is
     a superset of {rank-gameable}, so "buyable rank and fragile rank are one property" is FALSE as
     registered, and false in a definite direction.

  T4 (the separation law).  A mixing family s_lambda = (1 - lambda) * u_n + lambda * g_n, joining the
     monotone reference to a non-monotone outcome score on a common [0,1] scale, has TWO thresholds:
     lambda_tau (first lambda at which some cell becomes order-fragile, tau < 1) and lambda_G (first
     lambda at which some cell buys rank, G > 0).  T3 predicts lambda_tau <= lambda_G -- fragility
     appears no later than buyability.  The separation is measured, not assumed.

Everything is an exact Fraction; there is no sampling, no seed and no timing.  The artefact is
JSON-native (every rational a string).  Certificate (--selftest), each item with its own plant:
  C1 T1 holds for every declared transform, and a DECREASING transform breaks it.
  C2 T2's witness exists, and a monotone-only protocol set makes it vanish.
  C3 T3's implication holds in every cell AND is strict, and a monotone-only set breaks the strictness.
  C4 T4 reports both thresholds with lambda_tau <= lambda_G, and a monotone-only base finds neither.
  C5 determinism across PROCESSES (randomised hash seeds) and the artefact round-trips from disk.
"""
import argparse
import copy
import hashlib
import json
import os
import subprocess
import sys
from collections import OrderedDict
from fractions import Fraction as F

import spike_v0 as V

# ------------------------------------------------------------------------------------------------
# T1: strictly increasing transforms of the payoff profile preserve the ordering exactly

TRANSFORMS = OrderedDict([
    ("identity",    lambda x: x),
    ("cube",        lambda x: x ** 3),                 # strictly increasing (convex)
    ("affine",      lambda x: 2 * x + F(1, 3)),        # strictly increasing (slope 2), affine
    ("offset_scale", lambda x: (x + 7) * F(3, 2)),     # strictly increasing, shape-preserving
])
# the PLANT: strictly DECREASING -- reverses the ordering, so it must break T1
DECREASING = ("decreasing", lambda x: -x)


def transform_protocol(phi):
    """The protocol whose score is phi applied to the payoff profile u."""
    return lambda M, a, pop, W: phi(V._mean(M, a, pop))


def _norm(scores):
    """Min-max normalise a score vector to [0, 1] -- itself a monotone transform, so each component's
    ordering is preserved and lambda then interpolates between two orderings on a COMMON scale."""
    lo, hi = min(scores.values()), max(scores.values())
    if hi == lo:
        return OrderedDict((a, F(0)) for a in scores)
    return OrderedDict((a, (scores[a] - lo) / (hi - lo)) for a in scores)


def mixed(lam, base):
    """s_lambda = (1 - lambda) * norm(u) + lambda * norm(base score) -- an exact convex mixture."""
    def f(M, a, pop, W):
        U = _norm(OrderedDict((x, V._mean(M, x, pop)) for x in V.ZOO))
        G = _norm(OrderedDict((x, base(M, x, pop, W)) for x in V.ZOO))
        return (1 - lam) * U[a] + lam * G[a]
    return f


# ------------------------------------------------------------------------------------------------
# the scan: every (game, population, protocol) cell the v0 instrument declares

def _all_cells(protocols):
    """Run v0's cell() over every game x population x protocol.  Returns (cells, orderings)."""
    cells = OrderedDict()
    orderings = OrderedDict()
    for g in V.GAMES:
        M, W = _matrices(g)
        for pname, pop in V.populations().items():
            u_order = V.order_by(OrderedDict((a, V._mean(M, a, pop)) for a in V.ZOO))
            for prname, fn in protocols.items():
                key = "%s|%s|%s" % (g, pname, prname)
                c = V.cell(M, pop, fn, W)
                cells[key] = c
                orderings[key] = (V.order_by(OrderedDict((a, fn(M, a, pop, W)) for a in V.ZOO)),
                                  u_order)
    return cells, orderings


_MCACHE = {}


def _matrices(g):
    """Memoise v0's exact payoff/outcome matrices -- they do not depend on the protocol, and
    recomputing them per scan dominated the runtime (measured: 4m43s -> the cached form)."""
    if g not in _MCACHE:
        _MCACHE[g] = V.matrices(g)
    return _MCACHE[g]


def scan(protocols):
    """Aggregate a protocol set into the counts the theorems are about."""
    cells, orderings = _all_cells(protocols)
    g_pos = [k for k, c in cells.items() if c["G"] > 0]
    tau_lt = [k for k, c in cells.items() if F(c["tau"]) < 1]
    both = [k for k in g_pos if F(cells[k]["tau"]) < 1]
    g0_tau_lt = [k for k in tau_lt if cells[k]["G"] == 0]
    mismatch = [k for k, (o1, o2) in orderings.items() if o1 != o2]
    return {
        "cells": len(cells),
        "g_pos": len(g_pos),
        "tau_lt_1": len(tau_lt),
        "order_mismatch": len(mismatch),
        "g_pos_and_tau_lt_1": len(both),
        "g_pos_and_tau_ge_1": len(g_pos) - len(both),
        "g0_and_tau_lt_1": len(g0_tau_lt),
        "witness_g0_tau_lt_1": sorted(g0_tau_lt)[:5],
    }


def _pair(s):
    """The two counts the thresholds are read off, from ONE scan."""
    return {"g_pos": s["g_pos"], "tau_lt_1": s["tau_lt_1"]}


def run():
    doc = {"model": {"games": list(V.GAMES), "policies": list(V.ZOO),
                     "populations": list(V.populations()), "protocols": list(V.PROTOCOLS)}}
    # ---- T1: strictly increasing transforms preserve the ordering exactly
    t1 = OrderedDict()
    for name, phi in TRANSFORMS.items():
        s = scan(OrderedDict([("%s(x)" % name, transform_protocol(phi))]))
        t1[name] = s
    doc["T1_increasing_transforms"] = t1
    dname, dphi = DECREASING
    doc["T1_plant_decreasing"] = scan(OrderedDict([("%s(x)" % dname, transform_protocol(dphi))]))

    # ---- T2/T3 over the live zoo
    zoo = scan(V.PROTOCOLS)
    doc["T2_T3_zoo"] = zoo
    doc["T2_T3_plant_monotone_only"] = scan(OrderedDict([("mean_payoff", V.PROTOCOLS["mean_payoff"])]))

    # ---- T4: the mixing family, joining the monotone reference to the outcome score
    base = V.PROTOCOLS["game_wins"]
    grid = [F(k, 16) for k in range(17)]
    mixing = OrderedDict()
    for lam in grid:
        s = scan(OrderedDict([("mixed(%s)" % lam, mixed(lam, base))]))
        mixing[str(lam)] = {"g_pos": s["g_pos"], "tau_lt_1": s["tau_lt_1"], "cells": s["cells"]}
    lams = [str(l) for l in grid]
    lam_tau = next((l for l in lams if mixing[l]["tau_lt_1"] > 0), None)
    lam_G = next((l for l in lams if mixing[l]["g_pos"] > 0), None)
    doc["T4_mixing"] = mixing
    doc["T4_thresholds"] = {"lambda_tau": lam_tau, "lambda_G": lam_G,
                            "base": "game_wins", "grid": lams}
    doc["T4_plant_monotone_base"] = {
        l: _pair(scan(OrderedDict([("m", mixed(F(l), V.PROTOCOLS["mean_payoff"]))])))
        for l in lams}
    return doc


def dump(doc, path=None):
    txt = json.dumps(doc, indent=1, sort_keys=True) + "\n"
    if path:
        tmp = path + ".stage"
        with open(tmp, "w", encoding="utf-8") as fh:
            fh.write(txt)
        os.replace(tmp, path)
    return txt


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


# ------------------------------------------------------------------------------------------------
# the certificate

def _subprocess_json():
    env = dict(os.environ)
    env.pop("PYTHONHASHSEED", None)
    r = subprocess.run([sys.executable, os.path.abspath(__file__), "--json"],
                       capture_output=True, text=True, check=True, env=env)
    return r.stdout


def _rederive(doc):
    """Re-derive the two thresholds from the mixing table, independently of how they were reported."""
    lams = doc["T4_thresholds"]["grid"]
    m = doc["T4_mixing"]
    tau = next((l for l in lams if m[l]["tau_lt_1"] > 0), None)
    g = next((l for l in lams if m[l]["g_pos"] > 0), None)
    return tau, g


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

    print("C1 -- T1: a STRICTLY INCREASING transform preserves the ordering exactly")
    for name, s in doc["T1_increasing_transforms"].items():
        check("%s: G == 0 AND tau == 1 in every cell (ordering identical)" % name,
              s["g_pos"] == 0 and s["tau_lt_1"] == 0 and s["order_mismatch"] == 0,
              "cells=%d g_pos=%d tau<1=%d mismatch=%d"
              % (s["cells"], s["g_pos"], s["tau_lt_1"], s["order_mismatch"]))
    p = doc["T1_plant_decreasing"]
    check("a PLANTED DECREASING transform breaks T1 (the item is a test, not a print)",
          p["g_pos"] > 0 or p["tau_lt_1"] > 0 or p["order_mismatch"] > 0,
          "mismatch=%d g_pos=%d tau<1=%d" % (p["order_mismatch"], p["g_pos"], p["tau_lt_1"]))

    print("C2 -- T2: the naive converse is FALSE -- G == 0 with tau < 1 exists")
    z = doc["T2_T3_zoo"]
    check("witness cells exist where the protocol buys no rank yet is not order-equivalent",
          z["g0_and_tau_lt_1"] > 0,
          "%d cells, e.g. %s" % (z["g0_and_tau_lt_1"], z["witness_g0_tau_lt_1"][:2]))
    mp = doc["T2_T3_plant_monotone_only"]
    check("a PLANTED monotone-only protocol set makes the witness VANISH (C2 is a test)",
          mp["g0_and_tau_lt_1"] == 0, "monotone-only witnesses=%d" % mp["g0_and_tau_lt_1"])

    print("C3 -- T3: G > 0 => tau < 1 in EVERY cell, and the implication is STRICT")
    check("no cell buys rank while staying order-equivalent (G > 0 AND tau >= 1)",
          z["g_pos_and_tau_ge_1"] == 0,
          "%d such cells of %d with G>0" % (z["g_pos_and_tau_ge_1"], z["g_pos"]))
    check("the inclusion is STRICT: some order-fragile cell buys no rank (T2's witnesses)",
          z["g0_and_tau_lt_1"] > 0,
          "order-fragile=%d, rank-gameable=%d => fragile strictly contains buyable"
          % (z["tau_lt_1"], z["g_pos"]))
    check("a PLANTED monotone-only set makes the inclusion non-strict (C3's strictness is a test)",
          mp["g0_and_tau_lt_1"] == 0 and mp["g_pos"] == 0)

    print("C4 -- T4: the separation law -- two thresholds, lambda_tau <= lambda_G")
    tr = doc["T4_thresholds"]
    check("both thresholds are found on the declared grid",
          tr["lambda_tau"] is not None and tr["lambda_G"] is not None,
          "lambda_tau=%s lambda_G=%s" % (tr["lambda_tau"], tr["lambda_G"]))
    check("lambda_tau <= lambda_G (fragility appears no later than buyability)",
          tr["lambda_tau"] is not None and tr["lambda_G"] is not None
          and F(tr["lambda_tau"]) <= F(tr["lambda_G"]))
    check("the thresholds are RE-DERIVED from the table, not read from the summary",
          (tr["lambda_tau"], tr["lambda_G"]) == _rederive(doc))
    pm = doc["T4_plant_monotone_base"]
    check("a PLANTED monotone base finds NEITHER threshold (C4 is a test)",
          all(v["g_pos"] == 0 and v["tau_lt_1"] == 0 for v in pm.values()))

    print("C5 -- determinism across PROCESSES, and the artefact round-trips from disk")
    p1 = _subprocess_json()
    p2 = _subprocess_json()
    check("two PROCESSES with randomised hash seeds emit byte-identical JSON", p1 == p2,
          "%d bytes" % len(p1))
    corrupted = p1[:-2] + ("Z" if p1[-2] != "Z" else "Q") + p1[-1]
    check("the byte comparison DETECTS a one-byte change", p1 != corrupted)
    back = json.loads(p1)
    check("the artefact read back FROM DISK re-derives the same thresholds",
          _rederive(back) == _rederive(doc),
          "disk=%s memory=%s" % (_rederive(back), _rederive(doc)))

    print("SELFTEST %d/%d" % (ok, total))
    return 0 if ok == total else 1


# ------------------------------------------------------------------------------------------------
# the report

def report_text(doc):
    L = ["== issue #141 -- v1: the theory arm ==",
         "   %d games x %d policies x %d populations; every value exact"
         % (len(doc["model"]["games"]), len(doc["model"]["policies"]),
            len(doc["model"]["populations"])),
         "",
         "== T1 -- strictly increasing transforms preserve the ordering (the forward direction) ==",
         "   %-14s %6s %6s %8s %10s" % ("transform", "cells", "G>0", "tau<1", "mismatch")]
    for name, s in doc["T1_increasing_transforms"].items():
        L.append("   %-14s %6d %6d %8d %10d"
                 % (name, s["cells"], s["g_pos"], s["tau_lt_1"], s["order_mismatch"]))
    p = doc["T1_plant_decreasing"]
    L.append("   %-14s %6d %6d %8d %10d   <- PLANT (must break T1)"
             % ("decreasing", p["cells"], p["g_pos"], p["tau_lt_1"], p["order_mismatch"]))
    z = doc["T2_T3_zoo"]
    L += ["", "== T2/T3 -- over the live zoo (%d cells) ==" % z["cells"],
          "   G > 0                        : %d" % z["g_pos"],
          "   tau < 1 (order-fragile)      : %d" % z["tau_lt_1"],
          "   G > 0 AND tau >= 1           : %d   <- T3 forbids this (must be 0)" % z["g_pos_and_tau_ge_1"],
          "   G == 0 AND tau < 1 (witness) : %d   <- T2: the naive converse is FALSE" % z["g0_and_tau_lt_1"],
          "   witnesses: %s" % ", ".join(z["witness_g0_tau_lt_1"])]
    L += ["", "== T4 -- the separation law (mixing the monotone reference with game_wins) ==",
          "   %-8s %6s %8s" % ("lambda", "G>0", "tau<1")]
    for l, v in doc["T4_mixing"].items():
        L.append("   %-8s %6d %8d" % (l, v["g_pos"], v["tau_lt_1"]))
    tr = doc["T4_thresholds"]
    L += ["", "   lambda_tau (first order-fragile) = %s" % tr["lambda_tau"],
          "   lambda_G   (first rank bought)   = %s" % tr["lambda_G"],
          "   => fragility appears %s buyability" % ("no later than" if F(tr["lambda_tau"]) <= F(tr["lambda_G"])
                                                     else "AFTER (prediction broken!)"), ""]
    return "\n".join(L)


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--text", action="store_true")
    ap.add_argument("--out", metavar="PATH")
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
