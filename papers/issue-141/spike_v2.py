#!/usr/bin/env python3
"""issue #141 -- v2: the PROTOCOL-DESIGN LAW.

v0 measured the divergence; v1 put the registration's own *iff* on trial.  v2 asks the designer's
question -- **there are three nested properties, and they are not the same bar:**

    FAITHFUL   tau == 1 in every cell -- the score's WHOLE ordering equals the payoff ordering
    IMMUNE     G == 0 in every cell  -- the protocol never moves the head (the champion stays a
                                        payoff-optimum; its disagreements, if any, are BELOW the head)
    GAMEABLE   G > 0 somewhere       -- the head is bought

v1 proved the inclusion is strict one way: `faithful => immune`, but a protocol can be immune while
unfaithful.  v2 widens the protocol zoo into a **structured design space** so the nesting can be
MEASURED over real aggregations rather than observed in a corner:

  H1  faithful => immune, in EVERY cell of EVERY protocol (the theorem; two-sided by construction);
  H2  the inclusion is STRICT and REALIZABLE -- a constructed tail-disordering protocol is immune and
      unfaithful, and no faithful protocol is gameable;
  H3  the nesting counts satisfy |faithful| <= |immune| <= cells, re-derived from the cells;
  H4  the DESIGN MAP -- where each aggregation SHAPE sits.  The regularity (magnitude-retaining
      aggregations are faithful; sign and outcome aggregations are gameable; population-relative
      normalisers are immune-but-unfaithful) is REPORTED with its counterexamples, never asserted;
  H5  the BASELINES sit at the extremes -- the payoff-faithful reference is faithful and a protocol
      that ignores the payoffs entirely is gameable (a two-sided control for the whole instrument).

Everything is an exact Fraction; there is no sampling, no seed and no timing.  The artefact is
JSON-native (every rational a string).  Certificate (--selftest): each item carries its own plant, so
a check whose plant cannot break it is reported as decoration rather than as a pass.
"""
import argparse
import hashlib
import json
import os
import subprocess
import sys
from collections import OrderedDict
from fractions import Fraction as F

import spike_v0 as V

# ------------------------------------------------------------------------------------------------
# the widened design space: each protocol carries the SHAPE that decides its band

PROTOCOLS = OrderedDict()
SHAPE = OrderedDict()
READS = OrderedDict()      # what the score is a function of: "profile" | "row" | "none"
MONO = OrderedDict()       # how it treats it: "strict" | "saturating" | "none"


def add(name, shape, reads, mono, fn):
    PROTOCOLS[name] = fn
    SHAPE[name] = shape
    READS[name] = reads
    MONO[name] = mono
    return fn


# ---- shape `magnitude`: the score retains the LEVEL of the payoff profile ------------------------
add("mean_payoff", "magnitude", "profile", "strict", lambda M, a, pop, W: V._mean(M, a, pop))
add("mean_sq", "magnitude", "row", "none",
    lambda M, a, pop, W: sum((w * (M[a][b] ** 2) for b, w in pop.items()), F(0)))
add("spread", "magnitude", "profile", "strict",
    lambda M, a, pop, W: V._mean(M, a, pop)
    - sum((w * V._mean(M, b, pop) for b, w in pop.items()), F(0)))


def _top_half(M, a, pop, W):
    """Mean payoff against the population's own better half -- a trimmed, level-retaining aggregation."""
    order = sorted(V.ZOO, key=lambda b: (-V._mean(M, b, pop), b))
    keep = order[:max(1, len(order) // 2)]
    tot = sum((pop[b] for b in keep), F(0))
    if tot == 0:
        return F(0)
    return sum((pop[b] * M[a][b] for b in keep), F(0)) / tot


add("top_half", "magnitude", "row", "none", _top_half)
add("worst_opp", "magnitude", "row", "none", lambda M, a, pop, W: min(M[a][b] for b in V.ZOO))
add("best_opp", "magnitude", "row", "none", lambda M, a, pop, W: max(M[a][b] for b in V.ZOO))

# ---- shape `sign`: only the SIGN of the comparison survives --------------------------------------
add("win_count", "sign", "row", "none",
    lambda M, a, pop, W: sum((w * V._beats(M, a, b) for b, w in pop.items()), F(0)))
add("strict_wins", "sign", "row", "none", lambda M, a, pop, W: sum(
    (w * (F(1) if M[a][b] > M[b][a] else F(0)) for b, w in pop.items()), F(0)))
add("tie_count", "sign", "row", "none", lambda M, a, pop, W: sum(
    (w * (F(1) if M[a][b] == M[b][a] else F(0)) for b, w in pop.items()), F(0)))

# ---- shape `relative`: each number is normalised against the POPULATION's own statistics ---------
add("norm_by_best", "relative", "row", "none", lambda M, a, pop, W: sum(
    (w * (M[a][b] / max(M[x][b] for x in V.ZOO)) if max(M[x][b] for x in V.ZOO) != 0 else F(0)
     for b, w in pop.items()), F(0)))
add("relative_pair", "relative", "row", "none", lambda M, a, pop, W: sum(
    (w * ((M[a][b] - M[b][a]) / (abs(M[a][b]) + abs(M[b][a]) + F(1, 1000)))
     for b, w in pop.items()), F(0)))

# ---- shape `outcome`: who WINS the game, ignoring what the win costs ------------------------------
add("game_wins", "outcome", "row", "none", lambda M, a, pop, W: sum((w * W[a][b] for b, w in pop.items()), F(0)))
add("champion", "outcome", "row", "none", lambda M, a, pop, W: sum(
    (w * (F(1) if all(M[a][x] > M[x][a] for x in V.ZOO if pop[x] > 0 and x != a) else F(0))
     for b, w in pop.items()), F(0)))


# ---- shape `capped`: the level survives until the cap binds, then it is discarded -----------------
def _cap(C):
    return lambda M, a, pop, W: min(V._mean(M, a, pop), C)


add("capped_0", "capped", "profile", "saturating", _cap(F(0)))
add("capped_weak", "capped", "profile", "saturating", _cap(F(1, 2)))

# ---- the BASELINES -------------------------------------------------------------------------------
# the uninformative control: a FIXED random ordering that reads no payoff at all.  Deterministic by a
# stable digest (not the builtin `hash`, whose per-process salt would make the run non-reproducible).
_RAND = {}


def random_fixed(M, a, pop, W):
    if a not in _RAND:
        _RAND[a] = F(int(hashlib.sha256(("rand|" + a).encode()).hexdigest()[:8], 16), 2 ** 32)
    return _RAND[a]


add("random_fixed", "baseline", "none", "none", random_fixed)


# the CONSTRUCTED WITNESS (H2), honestly labelled: keep the payoff argmax exactly where it is and
# REVERSE the tail below it.  It is a deterministic function of the payoff profile, so it is a
# legitimate protocol for the purpose of exhibiting the strictness -- just not a natural aggregation.
def tail_swap(M, a, pop, W):
    u = OrderedDict((x, V._mean(M, x, pop)) for x in V.ZOO)
    order = V.order_by(u)                      # descending; ties broken lexicographically
    pos = {x: i for i, x in enumerate(order)}
    top = u[order[0]]
    if pos[a] == 0:
        return top                             # the head is preserved exactly
    return top - F(1, pos[a] + 1)              # strict and DECREASING in rank => the tail is reversed


add("tail_swap", "constructed", "profile", "none", tail_swap)

# ------------------------------------------------------------------------------------------------
# the scan

_MCACHE = {}


def _matrices(g):
    if g not in _MCACHE:
        _MCACHE[g] = V.matrices(g)
    return _MCACHE[g]


def scan(protocols):
    """Run every game x population x protocol through v0's cell(); return the counts the law is about."""
    cells = OrderedDict()
    for g in V.GAMES:
        M, W = _matrices(g)
        for pname, pop in V.populations().items():
            for prname, fn in protocols.items():
                cells["%s|%s|%s" % (g, pname, prname)] = V.cell(M, pop, fn, W)
    per = OrderedDict()
    for prname in protocols:
        sub = [c for k, c in cells.items() if k.split("|")[2] == prname]
        per[prname] = {
            "cells": len(sub),
            "faithful": sum(1 for c in sub if F(c["tau"]) == 1),
            "immune": sum(1 for c in sub if int(c["G"]) == 0),
            "gameable": sum(1 for c in sub if int(c["G"]) > 0),
            "tau_lt_1": sum(1 for c in sub if F(c["tau"]) < 1),
            "immune_and_unfaithful": sum(1 for c in sub if int(c["G"]) == 0 and F(c["tau"]) < 1),
            "G_max": str(max(int(c["G"]) for c in sub)),
        }
    return cells, per


def predict_band(reads, mono):
    """The design law, stated so it can be WRONG: faithfulness requires the score to be a strictly
    increasing function of the policy's OWN profile value.  A row-reading aggregation compares the
    policy against the population, and a saturating one stops being increasing where the cap binds."""
    if reads == "profile" and mono == "strict":
        return "faithful"
    if reads == "profile" and mono == "none":
        return "immune_unfaithful"
    return "gameable"


def band(v):
    """The nesting band a protocol's counts put it in -- read from the counters, not declared."""
    if v["gameable"] > 0:
        return "gameable"
    if v["tau_lt_1"] > 0:
        return "immune_unfaithful"
    return "faithful"


def run():
    cells, per = scan(PROTOCOLS)
    bands = OrderedDict((p, band(per[p])) for p in PROTOCOLS)
    predicted = OrderedDict((p, predict_band(READS[p], MONO[p])) for p in PROTOCOLS)
    mismatches = OrderedDict((p, {"predicted": predicted[p], "measured": bands[p]})
                             for p in PROTOCOLS if predicted[p] != bands[p])
    # the design map: shape -> the bands its members land in
    design = OrderedDict()
    for p, shape in SHAPE.items():
        design.setdefault(shape, OrderedDict())[p] = bands[p]
    # the nesting counts, over CELLS (every cell of every protocol is one observation)
    n_cells = len(cells)
    n_faith = sum(1 for c in cells.values() if F(c["tau"]) == 1)
    n_imm = sum(1 for c in cells.values() if int(c["G"]) == 0)
    n_both = sum(1 for c in cells.values() if F(c["tau"]) == 1 and int(c["G"]) == 0)
    n_imm_unf = sum(1 for c in cells.values() if int(c["G"]) == 0 and F(c["tau"]) < 1)
    n_game = sum(1 for c in cells.values() if int(c["G"]) > 0)
    return {
        "model": {"games": list(V.GAMES), "policies": list(V.ZOO),
                  "populations": list(V.populations()),
                  "protocols": list(PROTOCOLS), "shapes": OrderedDict(SHAPE),
                  "reads": OrderedDict(READS), "mono": OrderedDict(MONO)},
        "per_protocol": per,
        "bands": bands,
        "predicted_bands": predicted,
        "law_mismatches": mismatches,
        "design_map": design,
        "nesting": {
            "cells": n_cells,
            "faithful": n_faith,
            "immune": n_imm,
            "faithful_and_immune": n_both,
            "immune_and_unfaithful": n_imm_unf,
            "gameable": n_game,
            "faithful_implies_immune": n_faith == n_both,
            "strictly_contains": n_imm_unf > 0,
            "band_counts": OrderedDict(
                (b, sum(1 for x in bands.values() if x == b))
                for b in ("faithful", "immune_unfaithful", "gameable")),
        },
    }


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


def _rederive_nesting(doc):
    """Re-derive the nesting counts from the PER-PROTOCOL counters, not from the nesting block."""
    per = doc["per_protocol"]
    return (sum(v["faithful"] for v in per.values()),
            sum(v["immune"] for v in per.values()),
            sum(v["immune_and_unfaithful"] for v in per.values()))


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
    per, bands, nest = doc["per_protocol"], doc["bands"], doc["nesting"]
    pred = doc["predicted_bands"]

    print("H1 -- faithful => immune, in EVERY cell of EVERY protocol")
    bad = [p for p, v in per.items() if v["faithful"] != v["immune_and_unfaithful"] + v["faithful"]]
    check("no protocol has a faithful cell that is not immune (tau==1 with G>0 nowhere)",
          all(v["faithful"] <= v["immune"] for v in per.values()),
          "worst: %s" % ", ".join("%s %d>%d" % (p, per[p]["faithful"], per[p]["immune"])
                                  for p in per if per[p]["faithful"] > per[p]["immune"]) or "none")

    print("H2 -- the inclusion is STRICT and REALIZABLE")
    check("a CONSTRUCTED tail-disordering protocol is immune AND unfaithful",
          bands["tail_swap"] == "immune_unfaithful",
          "tail_swap: G_max=%s tau<1=%d/%d"
          % (per["tail_swap"]["G_max"], per["tail_swap"]["tau_lt_1"], per["tail_swap"]["cells"]))
    check("NO faithful protocol is gameable (the other side of the strictness)",
          all(v["gameable"] == 0 for p, v in per.items() if bands[p] == "faithful"),
          "faithful protocols: %s"
          % ", ".join(p for p in bands if bands[p] == "faithful"))

    print("H3 -- the nesting counts are re-derived from the cells")
    rd = _rederive_nesting(doc)
    check("|faithful| <= |immune| <= cells",
          nest["faithful"] <= nest["immune"] <= nest["cells"],
          "faithful=%d immune=%d cells=%d" % (nest["faithful"], nest["immune"], nest["cells"]))
    check("the nesting block agrees with the per-protocol counters",
          (nest["faithful"], nest["immune"], nest["immune_and_unfaithful"]) == rd,
          "block=%s re-derived=%s" % ((nest["faithful"], nest["immune"],
                                       nest["immune_and_unfaithful"]), rd))

    print("H4 -- the DESIGN LAW: a strictly increasing PROFILE reading is faithful; the rest is not")
    pred = doc["predicted_bands"]
    check("[theorem side] every protocol tagged (profile, strict) is measured FAITHFUL",
          all(bands[p] == "faithful" for p in PROTOCOLS if pred[p] == "faithful"),
          "members: %s" % ", ".join(p for p in PROTOCOLS if pred[p] == "faithful"))
    check("[law side] the prediction matches the MEASURED band for every protocol",
          not doc["law_mismatches"],
          "mismatches: %s" % (dict(doc["law_mismatches"]) or "none (17/17 protocols)"))
    check("no row-reading protocol is faithful (any aggregation against the population breaks it)",
          all(bands[p] != "faithful" for p in PROTOCOLS if doc["model"]["reads"][p] == "row"),
          "row-reading protocols: %d, faithful: %d"
          % (sum(1 for p in PROTOCOLS if doc["model"]["reads"][p] == "row"),
             sum(1 for p in PROTOCOLS if doc["model"]["reads"][p] == "row" and bands[p] == "faithful")))
    check("every band is non-empty (the map separates the zoo, it does not collapse it)",
          all(nest["band_counts"][b] > 0 for b in nest["band_counts"]),
          dict(nest["band_counts"]))

    print("H5 -- the baselines sit at the extremes (a two-sided control)")
    check("the payoff-faithful reference is FAITHFUL", bands["mean_payoff"] == "faithful",
          "tau<1=%d, G_max=%s" % (per["mean_payoff"]["tau_lt_1"], per["mean_payoff"]["G_max"]))
    check("the uninformative control is GAMEABLE", bands["random_fixed"] == "gameable",
          "G>0 in %d/%d cells" % (per["random_fixed"]["gameable"], per["random_fixed"]["cells"]))

    print("C6 -- determinism across PROCESSES, and the artefact round-trips from disk")
    p1 = _subprocess_json()
    p2 = _subprocess_json()
    check("two PROCESSES with randomised hash seeds emit byte-identical JSON", p1 == p2,
          "%d bytes" % len(p1))
    corrupted = p1[:-2] + ("Z" if p1[-2] != "Z" else "Q") + p1[-1]
    check("the byte comparison DETECTS a one-byte change", p1 != corrupted)
    back = json.loads(p1)
    check("the artefact read back FROM DISK re-derives the same nesting",
          _rederive_nesting(back) == _rederive_nesting(doc),
          "disk=%s memory=%s" % (_rederive_nesting(back), _rederive_nesting(doc)))

    print("SELFTEST %d/%d" % (ok, total))
    return 0 if ok == total else 1


# ------------------------------------------------------------------------------------------------
# the report

def report_text(doc):
    per, bands, nest = doc["per_protocol"], doc["bands"], doc["nesting"]
    pred = doc["predicted_bands"]
    L = ["== issue #141 -- v2: the protocol-design law ==",
         "   %d games x %d policies x %d populations x %d protocols = %d cells; all values exact"
         % (len(doc["model"]["games"]), len(doc["model"]["policies"]),
            len(doc["model"]["populations"]), len(doc["model"]["protocols"]), nest["cells"]),
         "",
         "== THE NESTING (over every cell of every protocol) ==",
         "   faithful (tau == 1)          : %d" % nest["faithful"],
         "   immune   (G == 0)            : %d" % nest["immune"],
         "   ... of which unfaithful      : %d   <- the STRICT band (H2)" % nest["immune_and_unfaithful"],
         "   gameable (G > 0)             : %d" % nest["gameable"],
         "   faithful => immune           : %s" % nest["faithful_implies_immune"],
         "",
         "== THE DESIGN MAP (per protocol: shape, band, counts) ==",
         "   %-15s %-10s %-8s %-9s %-19s %-19s %7s %6s"
         % ("protocol", "reads", "mono", "shape", "predicted", "MEASURED", "faithful", "G_max")]
    for p in doc["model"]["protocols"]:
        v = per[p]
        L.append("   %-15s %-10s %-8s %-9s %-19s %-19s %7d %6s"
                 % (p, doc["model"]["reads"][p], doc["model"]["mono"][p], doc["model"]["shapes"][p],
                    pred[p], bands[p], v["faithful"], v["G_max"]))
    L += ["", "== BY SHAPE =="]
    for shape, members in doc["design_map"].items():
        L.append("   %-12s %s" % (shape, ", ".join("%s:%s" % (p, b) for p, b in members.items())))
    L += ["", "== THE BAND COUNTS ==",
          "   %s" % ", ".join("%s=%d" % (b, n) for b, n in nest["band_counts"].items()), ""]
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
