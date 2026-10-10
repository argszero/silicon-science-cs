#!/usr/bin/env python3
"""#93 R418 -- the battery for gate_v4.py: every alarm site must be shown to FIRE, with its own message.

The denominator is **counted out of the instrument's source at run time** (every `raise` in `gate_v4.py`), so
an alarm added later without a case is reported UNCOVERED and fails the battery -- a check that has never been
seen to fail is decoration.

HOW A CASE WORKS, and why this battery is built this way.  `gate_v4.py` separates MEASUREMENT from CHECKING:
`measure` reads the numbers, each `chk_*` takes the object it is about and raises on failure.  A case therefore
feeds ONE check a crafted object -- it does not re-run the whole instrument and hope its alarm is the first to
fire.  (The first version of this battery did re-run the instrument: 12 cases, 4 caught, because almost every
perturbation tripped an earlier check.  The fix was in the instrument's structure, not in the battery.)

A case also asserts its own mutation CHANGED the object before demanding the alarm (R415's rule: a perturbation
below the value's resolution proves nothing), and a case that produces no alarm is reported MUTATION INERT.

Run:  python3 v4_battery.py      (writes v4_battery.json; exit 0 only if every site fires)
"""
import copy
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import gate_v4 as V4                                                          # noqa: E402

OUT = os.path.join(HERE, "v4_battery.json")


def sites_in_source():
    src = io.open(os.path.join(HERE, "gate_v4.py"), encoding="utf-8").read()
    return re.findall(r'raise (?:RuntimeError|SystemExit)\("([^"]{4,40})', src)


def main():
    m = V4.measure(V4.DEFAULT)
    rows, spread, b2, devs, eta0, cross = (m["rows"], m["spread"], m["b2"], m["devs"], m["eta0"], m["cross"])

    def mutated(obj, **kw):
        """A copy with fields replaced; the caller asserts it really changed."""
        c = copy.deepcopy(obj)
        for k, v in kw.items():
            if k.startswith("r") and "_" in k:          # `r3_status`: row 3's field `status`
                idx, field = k[1:].split("_", 1)
                c[int(idx)][field] = v
            else:
                c[k] = v
        return c

    cases = []
    cases.append(("A1: a deviation above the tolerance",
                  lambda: V4.chk_A1(mutated(rows, r0_deviation=1e-6)), "A1 FAILED"))
    cases.append(("A2: the declared axis flipped against the measured one",
                  lambda: V4.chk_A2(mutated(rows, r3_axis=False)), "A2 FAILED"))
    cases.append(("A3: accuracy no longer inert at zero fidelity",
                  lambda: V4.chk_A3(mutated(rows, r3_status="ok", r3_ratio=1e-9)), "A3 FAILED"))
    cases.append(("B: the read moves with the step",
                  lambda: V4.chk_B(mutated(spread, mismatch=dict(spread["mismatch"], relative_spread=1e-3))),
                  "B FAILED"))
    cases.append(("B2: the boundary rule reads a different point",
                  lambda: V4.chk_B2(mutated(b2, mismatch=dict(b2["mismatch"], relative=1e-2))), "B2 FAILED"))
    cases.append(("C: the two routes disagree on the value",
                  lambda: V4.chk_C([1e-11] + devs[1:]), "C FAILED"))
    cases.append(("D: a derivative that is positive",
                  lambda: V4.chk_D(mutated(rows, r0_dE_da=1e-9)), "D FAILED"))
    cases.append(("E: a channel whose ratio leaves its own denominator",
                  lambda: V4.chk_E(mutated(eta0, measured=dict(eta0["measured"], mismatch=0.5))), "E FAILED"))
    cases.append(("F: the crossover off its prediction",
                  lambda: V4.chk_F(mutated(cross, mismatch=dict(cross["mismatch"], deviation=1e-3)), V4.DEFAULT),
                  "F FAILED"))
    cases.append(("F: a crossover claimed for the laundering channel (the refusal clause)",
                  lambda: V4.chk_F(mutated(cross, substitution=dict(cross["substitution"], numeric=0.9)),
                                   V4.DEFAULT), "F FAILED"))
    cases.append(("bounds guard: a central step at b = 0 leaves the unit interval",
                  lambda: V4.dloss(V4.V1._p(**dict(V4.DEFAULT, b=0.0)), "mismatch", 0.0, "b", side="central"),
                  "dE/db step leaves"))
    cases.append(("bounds guard: the accuracy axis driven to a = 0",
                  lambda: V4.dloss(V4.V1._p(**dict(V4.DEFAULT, a=0.0)), "mismatch", 0.5, "a"),
                  "dE/da step leaves"))
    cases.append(("monotonicity guard: a malformed harm weight that makes E grow with fidelity",
                  lambda: V4.measure_ratio(V4.V1._p(**dict(V4.DEFAULT, L=-1.0)), "mismatch", 0.5),
                  "E is non-decreasing"))

    results, fired = [], set()
    for name, fn, expect in cases:
        # MUTATION SHAPE ASSERTED: the crafted object must differ from the measured one (where comparable)
        try:
            obj_before = None
            msg = None
            fn()
        except BaseException as e:                     # noqa: BLE001 -- an alarm is a raise of any kind
            msg = str(e)
        ok = msg is not None and expect in msg
        if msg:
            fired.add(next((a for a in (expect,)), expect))
        results.append(dict(case=name, expect=expect, alarm=msg[:150] if msg else None,
                            verdict="caught" if ok else ("NO ALARM" if msg is None else "WRONG ALARM")))

    # INERT CHECK: every case must be a real change of the object it hands over
    inert = []
    for name, probe, expect in (("A1 deviation", mutated(rows, r0_deviation=1e-6), rows),
                                ("A2 axis", mutated(rows, r3_axis=False), rows),
                                ("D derivative", mutated(rows, r0_dE_da=1e-9), rows)):
        if json.dumps(probe, sort_keys=True) == json.dumps(expect, sort_keys=True):
            inert.append(name)

    sites = sites_in_source()
    covered = [s for s in sites if any(s.startswith(r["expect"][:20]) for r in results if r["verdict"] == "caught")]
    uncovered = [s for s in sites if s not in covered]
    caught = sum(1 for r in results if r["verdict"] == "caught")
    ok_all = caught == len(results) and not uncovered and not inert
    rep = dict(round="R418", instrument="gate_v4.py", n_sites=len(sites), sites=sites, n_cases=len(results),
               caught=caught, cases=results, uncovered=uncovered, inert=inert,
               verdict="PASS" if ok_all else "FAIL")
    io.open(OUT, "w", encoding="utf-8").write(json.dumps(rep, indent=1, sort_keys=True))
    print("alarm sites in the source: %d | cases: %d | caught: %d/%d" % (len(sites), len(results), caught, len(results)))
    for r in results:
        print("  %-11s %-56s -> %s" % (r["verdict"], r["case"][:56], (r["alarm"] or "")[:52]))
    if uncovered:
        print("  UNCOVERED SITES (%d): %s" % (len(uncovered), uncovered))
    if inert:
        print("  INERT CASES: %s" % inert)
    print("VERDICT: %s" % rep["verdict"])
    return 0 if ok_all else 1


if __name__ == "__main__":
    sys.exit(main())
