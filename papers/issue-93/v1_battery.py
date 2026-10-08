#!/usr/bin/env python3
"""Mutation battery for #93 v1 (gate_v1.py): every alarm must be shown to FIRE.

Method (R408's, reused): for each `raise` site in the model, copy the file to a scratch path, apply ONE
targeted defect, run it, and require a non-zero exit carrying THAT site's message.  Every case mutates the
model or its reader -- none moves a threshold, because moving a threshold proves only that an `if` can run.

The denominator is derived from the SOURCE at run time (the `raise` lines are counted out of the file), not
from this case list, so an alarm added without a case shows up as a mismatch in the printed counts.

Carve-outs: where the defect aimed at a late alarm trips an earlier one first, the masking raise is replaced by
`pass` inside the SAME mutation and the case is marked CARVED, naming the alarm that has precedence.
"""
import io
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "gate_v1.py")
WORK = os.path.join(HERE, "v1_battery_work.py")
# The interpreter is a COORDINATE of the run, not a constant of this file.  reproduce.sh declares it
# with `PYTHON=...` and exports it; the battery must spawn the SAME interpreter, or the run silently
# splits across two of them (a numpy-less default fails the gates while these still pass).
PY = os.environ.get("PYTHON") or sys.executable

R_CONT = 'raise RuntimeError("v1 does not reduce to v0 at b = 1: %.3e" % worst_cont)'
R_CURV = ('raise RuntimeError("the value is NOT affine in coverage: %d cells show curvature, e.g. %s"\n'
          '                           % (len(bad), bad[:3]))')
R_SLOPE = 'raise RuntimeError("the closed-form slope does not match the enumeration: %.3e" % worst_slope)'
R_BS = 'raise RuntimeError("the closed-form b* does not match the bisected zero: %.3e" % worst_b)'
R_MC = 'raise RuntimeError("the Monte Carlo route missed its interval in %d cells" % (len(mc_rows) - covered))'
R_MCBIAS = 'raise RuntimeError("the Monte Carlo estimate is biased at b < 1: %.3e +- %.3e" % (bias, bias_se))'

CASES = [
    ("fatigue_state_space", "the fatigue arm's state space must sum to 1",
     [("                total += prob", "                total += prob * (1.0 + 1e-3)")],
     "does not sum to 1", "direct"),

    ("continuity_with_v0", "v1 must reduce to v0 at b = 1",
     # the mutation must bite AT b = 1: the unfaithful branch carries probability 1 - b = 0 there, so mutating
     # it is inert and the case would "fire" for the wrong reason.  Marking a faithful draw as substituted
     # changes the severity where this control reads.
     [("                    render_harm, exec_harm, binds, substituted = P_harm, P_harm, True, False",
       "                    render_harm, exec_harm, binds, substituted = P_harm, P_harm, False, False")],
     "does not reduce to v0", "direct"),

    ("affineness_curvature", "the value must be affine in coverage",
     # The curvature check reads V0.enumerate_exact, so the mutation must reach THAT read: injecting
     # curvature into the values the detector is handed is the standard way to test a detector (a
     # mutation inside enum_fatigue is aimed at a function this check never calls).
     [("                vals = [V0.enumerate_exact(pr, s, variant=variant, b=b, screen_only=False)[0] for s in s_trip]",
       "                vals = [V0.enumerate_exact(pr, s, variant=variant, b=b, screen_only=False)[0] + 0.01 * s * s for s in s_trip]")],
     "NOT affine in coverage", "direct (the read value is given curvature -- the detector's own object)"),

    ("slope_law", "the closed-form slope must match the enumeration",
     [("    return L * pi * b * a - c - cb * (1.0 - pi) * b * f\n", "    return L * pi * b * a * 1.001 - c - cb * (1.0 - pi) * b * f\n"),
      (R_CURV, "pass")],
     "closed-form slope does not match", "CARVED (a wrong slope coefficient also makes the value non-affine)"),

    ("sign_law_bstar", "the closed-form b* must match the bisected zero",
     [("    num = c + eta * L * (1.0 - pi)\n", "    num = c + 1.05 * eta * L * (1.0 - pi)\n")],
     "closed-form b* does not match the bisected zero", "direct"),

    ("channel_asymmetry", "the laundering term must hold the higher bar",
     [("        return ((c + cb * (1.0 - pi) * f) / (L * pi) - f) / (a - f)\n",
       "        return ((c + cb * (1.0 - pi) * f) / (L * pi) - f) / (a - f) + 0.5\n"),
      (R_BS, "pass")],
     "not asymmetric as registered", "CARVED (a moved b* is caught by the b* law first)"),

    ("b_independent_variant_skipped", "the b-independent variant must not get a b*",
     [("            if v0_ * v1_ >= 0.0:", "            if v0_ * v1_ > 1e9:"),
      (R_BS, "pass")],
     "expected the b-independent variant to be skipped", "CARVED (with the guard off this variant is bisected and the b* law fires first)"),

    ("mc_coverage", "the drawn interval must cover the enumeration at b < 1",
     [("            draw, CI, se, _ = V0.simulate(pr, 0.6, variant=variant, b=b, n=400000,\n"
       "                                          seed=8300 + int(100 * b) + len(variant), screen_only=False)",
       "            draw, CI, se, _ = V0.simulate(pr, 0.6, variant=variant, b=b, n=400000,\n"
       "                                          seed=8300 + int(100 * b) + len(variant), screen_only=False)\n"
       "            CI = (CI[0] - 0.25, CI[1] - 0.25)")],
     "missed its interval", "direct"),

    ("mc_bias", "the drawn estimate must be unbiased at b < 1",
     [("            draw, CI, se, _ = V0.simulate(pr, 0.6, variant=variant, b=b, n=400000,\n"
       "                                          seed=8300 + int(100 * b) + len(variant), screen_only=False)",
       "            draw, CI, se, _ = V0.simulate(pr, 0.6, variant=variant, b=b, n=400000,\n"
       "                                          seed=8300 + int(100 * b) + len(variant), screen_only=False)\n"
       "            draw = draw + 0.5          # the interval is untouched, so only the BIAS alarm can see this")],
     "biased at b < 1", "direct (the estimate moves while its interval does not)"),

    ("fatigue_floor_separation", "the floor must separate corner from interior",
     # An inert-coupling test: with kappa = 1 but the coupling dropped, every argmax is a corner again,
     # which is what the floor-separation alarm is for.  (A small sensitivity boost leaves the pattern
     # intact and the case ran to completion -- a mutation must change the property, not its magnitude.)
     [("    a_s = a * (1.0 - kappa * s)", "    a_s = a")],
     "does not separate corner from interior", "direct (the coupling is removed while kappa stays 1)"),

    ("floor_is_straddled", "the floor must be read on both sides",
     [("        for b in (0.05, 0.1, 0.12, 0.13, 0.15, 0.2, 0.25, 0.5, 0.75, 1.0):",
       "        for b in (0.5, 0.75, 1.0):")],
     "the floor is not straddled", "direct"),

    ("fatigue_sstar_closed_form", "the closed-form vertex must match the grid argmax",
     [("    return num / (2.0 * kappa * L * pi * b * a)", "    return num / (2.0 * kappa * L * pi * b * a) + 0.05")],
     "does not match the grid argmax", "direct"),
]


def apply_edits(text, edits):
    for old, new in edits:
        n = text.count(old)
        if n != 1:
            raise SystemExit("mutation anchor occurs %d times (need exactly 1):\n%r" % (n, old[:110]))
        text = text.replace(old, new)
    return text


def main():
    src = io.open(SRC).read()
    sites = [l.strip() for l in src.splitlines() if l.strip().startswith("raise RuntimeError(")]
    rows, bad = [], []
    for name, object_, edits, expect, kind in CASES:
        io.open(WORK, "w").write(apply_edits(src, edits))
        proc = subprocess.run([PY, WORK], capture_output=True, text=True, timeout=300)
        err = (proc.stderr.strip().splitlines() or [""])[-1]
        fired = proc.returncode != 0 and expect in (proc.stderr + proc.stdout)
        rows.append(dict(check=name, object=object_, kind=kind, fired=bool(fired),
                         returncode=proc.returncode, error=err))
        if not fired:
            bad.append(name)
        print("%-32s %-6s rc=%-3s %-9s %s" % (name, "FIRED" if fired else "MISSED", proc.returncode,
                                              "carved" if kind.startswith(("CARVED", "WRONG")) else "direct",
                                              err[:92]))
    print("\n%d/%d alarms fired" % (len(rows) - len(bad), len(rows)))
    print("the model carries %d raise sites; this battery has %d cases" % (len(sites), len(CASES)))
    io.open(os.path.join(HERE, "v1_battery.json"), "w").write(json.dumps(
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
