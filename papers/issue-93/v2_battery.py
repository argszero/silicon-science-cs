#!/usr/bin/env python3
"""Mutation battery for #93 v2 (gate_v2.py): every alarm must be shown to FIRE.

Method (R408/R410's, reused): one targeted defect per `raise` site, applied to a throwaway copy, run, and
required to exit non-zero carrying THAT site's message.  Mutations edit the model or what it is read with; none
moves a threshold.  The denominator is counted out of the source at run time, so an alarm added without a case
shows up as a mismatch in the printed counts.  Carve-outs neutralise the masking raise in the SAME mutation and
name the alarm that has precedence.
"""
import io
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "gate_v2.py")
WORK = os.path.join(HERE, "v2_battery_work.py")
# The interpreter is a COORDINATE of the run, not a constant of this file.  reproduce.sh declares it
# with `PYTHON=...` and exports it; the battery must spawn the SAME interpreter, or the run silently
# splits across two of them (a numpy-less default fails the gates while these still pass).
PY = os.environ.get("PYTHON") or sys.executable

R_P1 = 'raise RuntimeError("a gated design does not reduce to v1\'s screening case: %.3e" % worst)'
R_MC = 'raise RuntimeError("the Monte Carlo route missed its interval in %d cells" % (len(mc) - covered))'
R_ORDER = 'raise RuntimeError("the design ordering misses the external-validation arm: %s" % p5)'
R_P2 = 'raise RuntimeError("the check\'s value does not follow sigma_v: %s" % p2)'
R_P6A = 'raise RuntimeError("D3\'s attack success is not the R-invisible share: %s" % p6)'
R_P6B = 'raise RuntimeError("the anchor\'s zero-attack case is not isolated: %s" % p6)'

CASES = [
    ("reduces_to_v1_screening", "a gated design with a perfect channel must be v1's screening case",
     # the clean class IS v1's screening case, so the mutation must change its behaviour: making its blocks
     # non-binding changes the loss away from v1's value at a perfect channel.
     [("                    render_harm, exec_harm, binds = P_harm, P_harm, True",
       "                    render_harm, exec_harm, binds = P_harm, P_harm, False")],
     "does not reduce to v1", "direct (the clean class stops binding)"),

    ("no_gate_loss", "the no-gate design's loss must be L*pi",
     [("    if not spec[\"gate\"]:\n        return L * pi, dict(harm=pi, attention=0.0, false_block=0.0, attack_success=None)",
       "    if not spec[\"gate\"]:\n        return L * pi * 1.001, dict(harm=pi, attention=0.0, false_block=0.0, attack_success=None)")],
     "loss is not L*pi", "direct"),

    ("no_gate_value", "the no-gate design's VALUE must be 0 (E1 = E0), a different object from its loss",
     [("def value(params, s, design, defect=None):\n    \"\"\"V = E0 - E1, the design's per-action value against the no-gate baseline.\"\"\"\n    loss, _ = enum_design(params, s, design, defect)",
       "def value(params, s, design, defect=None):\n    \"\"\"V = E0 - E1, the design's per-action value against the no-gate baseline.\"\"\"\n    loss, _ = enum_design(params, s, design, defect)\n    if design == \"D0\":\n        return 0.1")],
     "no-gate design's value is not 0", "direct (the value and the loss are read at their own alarms)"),

    ("design_ordering", "the ordering must match the external-validation arm",
     [("    if d[\"sigma_v\"] > 0:\n        out.append((\"subv\", d[\"sigma_v\"], spec[\"check\"] in (\"R\", \"request\")))",
       "    if d[\"sigma_v\"] > 0:\n        out.append((\"subv\", d[\"sigma_v\"], False))")],
     "external-validation arm", "direct (the check stops catching anything)"),

    ("check_value_follows_sigma_v", "the check's value must follow the R-visible mass",
     [("    if d[\"sigma_i\"] > 0:\n        out.append((\"subi\", d[\"sigma_i\"], spec[\"check\"] == \"request\"))",
       "    if d[\"sigma_i\"] > 0:\n        out.append((\"subi\", d[\"sigma_i\"], spec[\"check\"] in (\"R\", \"request\")))")],
     "value does not follow sigma_v", "direct (the same-R check now catches the invisible class, so its value no longer tracks sigma_v)"),

    ("blind_spot_follows_sigma_i", "the blind spot must follow the R-invisible mass",
     [("    if d[\"sigma_v\"] > 0:\n        out.append((\"subv\", d[\"sigma_v\"], spec[\"check\"] in (\"R\", \"request\")))",
       "    if d[\"sigma_v\"] > 0:\n        out.append((\"subv\", d[\"sigma_v\"], spec[\"check\"] == \"request\"))"),
      (R_ORDER, "pass"), (R_P2, "pass")],
     "blind spot does not follow sigma_i", "CARVED (the ordering alarm reads the same table and fires first)"),

    ("display_class_blind", "the check must not repair the display class",
     # the display class is absent for a canonical design because `p_display` is zeroed, not because a
     # later branch hides it; the mutation re-admits it, which is what a design that "repairs" the class
     # by reading R would look like from the inside.
     # the rule has TWO carriers -- the enumeration and the drawing -- and the anchor is disambiguated by
     # what follows each: a mutation that moved one only would make the two routes disagree about the model,
     # which is its own case below.
     [("    p_display = 0.0 if spec[\"canonical\"] else d[\"delta\"]\n    total = p_display",
       "    p_display = d[\"delta\"]\n    total = p_display"),
      ("    p_display = 0.0 if spec[\"canonical\"] else d[\"delta\"]\n    p_subv",
       "    p_display = d[\"delta\"]\n    p_subv")],
     "appears to repair the display class", "direct (the canonical rendering stops mattering)"),

    ("routes_agree_on_the_model", "the enumeration and the drawing must apply the SAME rule",
     # this is the invariant that caught this round's own defect: the two routes had different partitions
     # (1.104 vs 1.0) and, then, different false-block counterfactuals.  Moving the rule in ONE carrier only
     # must show up as the routes disagreeing, not as a silent 25-standard-error bias.
     # the mutation moves the DRAWING's carrier only: every exact read (P1/P2/P3/P4/P6) is untouched, so the
     # only alarm that can see it is the route comparison -- which is exactly why the comparison exists.  Moving
     # the enumeration's carrier instead changes an exact design value and the P4 alarm fires first.
     [("    p_display = 0.0 if spec[\"canonical\"] else d[\"delta\"]\n    p_subv",
       "    p_display = 0.0 if spec[\"canonical\"] else 0.0 * d[\"delta\"]\n    p_subv")],
     "missed its interval", "direct (one carrier moved, the other route notices)"),

    ("defect_params_exceed_one", "defect masses that exceed 1 must be refused before any reading",
     [("DEFECT = dict(delta=0.30, sigma_v=0.20, sigma_i=0.10)",
       "DEFECT = dict(delta=0.90, sigma_v=0.20, sigma_i=0.10)")],
     "defect parameters exceed 1", "direct (three masses cannot sum above 1)"),

    ("class_masses_sum_to_one", "the channel's classes must PARTITION its state space",
     # this is the assertion the first version of v2 lacked; it is what caught the pipeline product
     # (1-delta)(1-sigma_v)(1-sigma_i), whose masses summed to 1.104 while the drawing route used a
     # partition of the same parameters.  The mutation reproduces that shape: one class inflated.
     [("    out = [(\"clean\", 1.0 - total, False)]",
       "    out = [(\"clean\", 1.0 - total + 0.1, False)]")],
     "do not sum to 1", "direct (a class mass inflated above its share)"),

    ("anchor_zero_isolated", "the zero-attack case must be isolated to a fully visible channel",
     [("        exp = dd[\"sigma_i\"] / (dd[\"sigma_v\"] + dd[\"sigma_i\"])",
       "        exp = 0.5 * dd[\"sigma_i\"] / (dd[\"sigma_v\"] + dd[\"sigma_i\"])")],
     "not the R-invisible share", "direct"),

    ("anchor_zero_case", "the anchor's zero case must actually be zero",
     [('for dd, label in ((dict(DEFECT, sigma_v=0.3, sigma_i=0.0), "channel fully R-visible"),',
       'for dd, label in ((dict(DEFECT, sigma_v=0.3, sigma_i=0.01), "channel fully R-visible"),')],
     "zero-attack case is not isolated", "direct"),

    ("rederived_closes_channel", "the re-derived check must close the channel",
     [("    if d[\"sigma_i\"] > 0:\n        out.append((\"subi\", d[\"sigma_i\"], spec[\"check\"] == \"request\"))",
       "    if d[\"sigma_i\"] > 0:\n        out.append((\"subi\", d[\"sigma_i\"], False))"),
      (R_ORDER, "pass")],
     "blind spot does not follow sigma_i",
     "CARVED (P3 reads the same V(D4) - V(D3) table and fires first; P6's own site is reached by its sibling "
     "case, which moves the reported attack share instead of the caught set)"),

    ("mc_coverage", "the drawn interval must cover the exact design values",
     [("    return loss, (loss - 1.96 * se, loss + 1.96 * se), attack",
       "    return loss, (loss - 0.196 * se, loss + 0.196 * se), attack")],
     "missed its interval", "direct (the interval is narrowed around a draw the exact value now misses)"),

    ("mc_bias", "the drawn design values must be unbiased",
     [("        mc_v = base[\"L\"] * base[\"pi\"] - draw",
       "        mc_v = base[\"L\"] * base[\"pi\"] - draw\n        draw = draw + 0.5"),
      (R_MC, "pass")],
     "drawn design values are biased", "CARVED (a biased draw also leaves the interval)"),
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
        print("%-30s %-6s rc=%-3s %-9s %s" % (name, "FIRED" if fired else "MISSED", proc.returncode,
                                              "carved" if kind.startswith(("CARVED", "WRONG")) else "direct",
                                              err[:90]))
    print("\n%d/%d alarms fired" % (len(rows) - len(bad), len(rows)))
    print("the model carries %d raise sites; this battery has %d cases" % (len(sites), len(CASES)))
    io.open(os.path.join(HERE, "v2_battery.json"), "w").write(json.dumps(
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
