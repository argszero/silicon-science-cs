#!/usr/bin/env python3
"""Mutation battery for #93 v3 (gate_v3.py): every alarm must be shown to FIRE.

Method (R408/R410/R411's, reused): one targeted defect per `raise` site, applied to a throwaway copy, run, and
required to exit non-zero carrying THAT site's message.  The denominator is counted out of the source at run
time, so an alarm added without a case shows up as a mismatch in the printed counts.  A mutation that is masked
by a raise earlier in the same run is a CARVE-OUT: it neutralises the masking raise in the SAME mutation and
names the alarm that has precedence.

The round's own lesson is applied to the cases themselves: a mutation must change the PROPERTY the alarm reads,
at the code path the alarm reads it from.  Two of the seven cases below therefore move a read's OBJECT (the band
is read off a different arm; the determinism control compares two different seeds) rather than a number, because
those alarms' objects are reads.
"""
import io
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "gate_v3.py")
WORK = os.path.join(HERE, "v3_battery_work.py")
# The interpreter is a COORDINATE of the run, not a constant of this file.  reproduce.sh declares it
# with `PYTHON=...` and exports it; the battery must spawn the SAME interpreter, or the run silently
# splits across two of them (a numpy-less default fails the gates while these still pass).
PY = os.environ.get("PYTHON") or sys.executable

R_COVER = ("raise RuntimeError(\"the drawn intervals' coverage rate is not consistent with the nominal 95%%: %s\"")
R_EXACT = ('raise RuntimeError("the no-gate route is not exact on some reading: %s" % degenerate[:2])')
R_MONO = ('raise RuntimeError("the exact design ladder is not strictly monotone at every cell: %s"')
R_UNAN = ('raise RuntimeError("a resolvable ordering reading is not unanimous across streams: %s" % failed)')
R_EXT = ('raise RuntimeError("the external-validation arm does not reproduce the published orderings: %s"')
R_HEAD = ('raise RuntimeError("the headline does not appear anywhere on the parameter grid: the phenomenon and the "')
R_CTL = ('raise RuntimeError("a control failed: %s" % res["controls"])')

CASES = [
    ("coverage_rate_is_a_rate",
     "the drawn intervals must cover the exact value at the rate they claim (95 %)",
     [("                draw, ci, attack = V2.simulate_design(params, S, design, n=N_DRAW, seed=seed)",
       "                draw, ci, attack = V2.simulate_design(params, S, design, n=N_DRAW, seed=seed)\n"
       "                ci = (draw - 0.2 * (draw - ci[0]), draw + 0.2 * (ci[1] - draw))")],
     "coverage rate is not consistent", "direct (intervals 5x too narrow)"),

    ("no_gate_route_is_exact",
     "the no-gate design's route must be exact (it has no sampling), so its point must equal the enumeration",
     [("                draw, ci, attack = V2.simulate_design(params, S, design, n=N_DRAW, seed=seed)",
       "                draw, ci, attack = V2.simulate_design(params, S, design, n=N_DRAW, seed=seed)\n"
       "                draw = draw + (1e-9 if design == \"D0\" else 0.0)")],
     "no-gate route is not exact", "direct (a zero-width reading that disagrees with the enumeration)"),

    ("exact_ladder_is_monotone",
     "the exact design ladder must be strictly monotone at every cell",
     [("    pairs = ((\"D1\", \"D2\"), (\"D2\", \"D3\"), (\"D3\", \"D4\"))",
       "    pairs = ((\"D1\", \"D2\"), (\"D2\", \"D3\"), (\"D4\", \"D3\"))")],
     "exact design ladder is not strictly monotone", "direct (the ladder's last pair read backwards)"),

    ("resolvable_pair_is_unanimous",
     "a pair whose exact gap exceeds the streams' resolution must be unanimous in sign",
     [("            drawn[seed] = {d: params[\"L\"] * params[\"pi\"]\n"
       "                              - V2.simulate_design(params, S, d, n=N_DRAW, seed=seed)[0]\n"
       "                           for d in V2.DESIGNS}",
       "            drawn[seed] = {d: params[\"L\"] * params[\"pi\"]\n"
       "                              - V2.simulate_design(params, S, d, n=N_DRAW, seed=seed)[0]\n"
       "                              - (0.05 if (d == \"D2\" and seed == STREAMS[0]) else 0.0)\n"
       "                           for d in V2.DESIGNS}")],
     "not unanimous across streams", "direct (one stream drifts on one arm)"),

    ("external_band_is_the_unbound_arm",
     "the attack-success band is a claim about the UNBOUND arm -- the published 68-100 % band is its object",
     [("    band = dict(published=[0.68, 1.00], unbound_atk=atk[\"D1\"], inside=bool(0.68 <= atk[\"D1\"] <= 1.00),",
       "    band = dict(published=[0.68, 1.00], unbound_atk=atk[\"D3\"], inside=bool(0.68 <= atk[\"D3\"] <= 1.00),")],
     "does not reproduce the published orderings", "direct (the band read off the checked arm instead)"),

    ("headline_appears_on_the_grid",
     "the net-harmful gate must appear somewhere on the declared grid, or the grid and the phenomenon disagree",
     [("            if v < -1e-12:", "            if v < -1e9:")],
     "headline does not appear anywhere", "direct (the detector's object set emptied)"),

    ("controls_can_fail",
     "the determinism control must compare the SAME stream with itself",
     [("    c2 = all(V2.simulate_design(base, S, d, n=N_DRAW, seed=STREAMS[0])\n"
       "             == V2.simulate_design(base, S, d, n=N_DRAW, seed=STREAMS[0]) for d in V2.DESIGNS)",
       "    c2 = all(V2.simulate_design(base, S, d, n=N_DRAW, seed=STREAMS[0])\n"
       "             == V2.simulate_design(base, S, d, n=N_DRAW, seed=STREAMS[1]) for d in V2.DESIGNS)")],
     "a control failed", "direct (the control reads two different streams)"),
]


def apply_edits(text, edits):
    for old, new in edits:
        n = text.count(old)
        if n != 1:
            raise SystemExit("mutation anchor occurs %d times (need exactly 1):\n%r" % (n, old[:120]))
        text = text.replace(old, new)
    return text


def main():
    src = io.open(SRC).read()
    sites = [l.strip() for l in src.splitlines() if l.strip().startswith("raise RuntimeError(")]
    rows, bad = [], []
    for name, object_, edits, expect, kind in CASES:
        io.open(WORK, "w").write(apply_edits(src, edits))
        proc = subprocess.run([PY, WORK], capture_output=True, text=True, timeout=900)
        err = (proc.stderr.strip().splitlines() or [""])[-1]
        fired = proc.returncode != 0 and expect in (proc.stderr + proc.stdout)
        rows.append(dict(check=name, object=object_, kind=kind, fired=bool(fired),
                         returncode=proc.returncode, error=err))
        if not fired:
            bad.append(name)
        print("%-34s %-6s rc=%-3s %-8s %s" % (name, "FIRED" if fired else "MISSED", proc.returncode,
                                              "carved" if kind.startswith("CARVED") else "direct", err[:84]))
    print("\n%d/%d alarms fired" % (len(rows) - len(bad), len(rows)))
    print("the model carries %d raise sites; this battery has %d cases" % (len(sites), len(CASES)))
    io.open(os.path.join(HERE, "v3_battery.json"), "w").write(json.dumps(
        dict(cases=rows, all_fired=not bad, missed=bad, raise_sites_in_model=len(sites),
             cases_run=len(CASES)), indent=1, sort_keys=True))
    if os.path.exists(WORK):
        os.remove(WORK)
    if bad:
        print("MISSED: %s" % ", ".join(bad))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
