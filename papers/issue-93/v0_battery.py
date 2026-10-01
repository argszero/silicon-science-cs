#!/usr/bin/env python3
"""Mutation battery for #93 v0 (gate_v0.py): each alarm must be shown to FIRE.

Method.  For every `raise` site in the model, copy the file to a scratch path, apply a targeted defect, run it,
and require a non-zero exit whose message is that site's.  A check with no case that reaches it is decoration.

Carve-out.  Several controls share the model, so a defect aimed at a late control can trip an early one first.
Where that happens the masking raise is replaced by `pass` in the SAME mutation and the case is marked CARVED --
the note travels with the result, so the finding is not "the alarm fired" but "the alarm is reachable once the
earlier one is out of the way".  A carve-out is evidence too: it names which alarm has precedence.

Every case mutates the MODEL or its reader, never a threshold: moving a threshold proves only that an `if` can
run, not that the condition it guards can be false.
"""
import io
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = "/Users/argszero/scm/github.com/argszero/silicon-science-cs/papers/issue-93/research/gate_v0.py"
WORK = os.path.join(HERE, "v0_battery_work.py")
PY = "/usr/bin/python3"

# --- the masking raises, used as carve-outs (each occurs exactly once) -------------------------------------
R_AB = 'raise RuntimeError("routes A and B disagree beyond floating point: %.3e" % worst)'
R_MISS = ('raise RuntimeError("the Monte Carlo route missed its interval in %d of %d cells" % (misses,\n'
          '                                                                                            len(closure)))')
R_BIAS = 'raise RuntimeError("the Monte Carlo estimator is biased: %.3e +- %.3e" % (bias, bias_se))'
R_FREQ = 'raise RuntimeError("the drawn frequencies are outside Monte Carlo error of the enumeration")'
R_C1_EXACT = 'raise RuntimeError("s=0 is not the no-gate baseline: %.17g vs %.17g" % (B0, p0["pi"] * p0["L"]))'
R_C1_CI = 'raise RuntimeError("the no-gate baseline left the drawn interval")'
NARROW = ("return loss, (loss - 1.96 * se, loss + 1.96 * se), se, dict(",
          "return loss, (loss - 0.196 * se, loss + 0.196 * se), se, dict(")
GUARD_ENUM = """    if screen_only and b < 1.0:
        raise RuntimeError("v0 reads the screening case only (b=1); the map is a later round's object")
    pi, a, f = params["pi"], params["a"], params["f"]
    L, c, cb = params["L"], params["c"], params["cb"]
    eta = params["eta"]                    # the harm of a SUBSTITUTED action, as a fraction of L"""
GUARD_SIM = """    if screen_only and b < 1.0:
        raise RuntimeError("v0 reads the screening case only (b=1); the map is a later round's object")
    pi, a, f = params["pi"], params["a"], params["f"]
    L, c, cb = params["L"], params["c"], params["cb"]
    eta = params["eta"]\n"""
LOSS_LINE = "    loss = (float(np.sum(severity * (exec_harm & executes))) + c * att_count + cb * fb_count) / n"
PER_LINE = "    per = (severity * (exec_harm & executes).astype(float)"

CASES = [
    # ---- the state space and the closure -----------------------------------------------------------------
    ("state_space_sums_to_1", "the state space must sum to 1",
     [("        for esc in (True, False):", "        for esc in (True,):")],
     "does not sum to 1", "direct"),

    ("closure_A_vs_B", "routes A and B must agree to floating point",
     [("return L * pi * ((1.0 - s) + s * (1.0 - a)) + c * s + cb * (1.0 - pi) * s * f",
       "return L * pi * ((1.0 - s) + s * (1.0 - a)) + c * s * 1.001 + cb * (1.0 - pi) * s * f")],
     "routes A and B disagree", "direct"),

    ("closure_coverage_alarm", "the drawn interval must cover the exact value",
     [NARROW], "missed its interval in", "direct"),

    ("closure_bias_alarm", "the estimator must be unbiased",
     [(LOSS_LINE, "    loss = (float(np.sum(1.05 * severity * (exec_harm & executes))) + c * att_count + cb * fb_count) / n"),
      (PER_LINE, "    per = (1.05 * severity * (exec_harm & executes).astype(float)"),
      (R_MISS, "pass")],
     "estimator is biased", "CARVED (both expressions move together, so the coverage alarm goes first)"),

    ("interval_centre_matches_estimate", "the reported estimate and the interval's centre are one quantity",
     [(LOSS_LINE, LOSS_LINE[:-4] + " * 1.001")],
     "they disagree", "direct (the battery is what found this pair untied)"),

    ("frequency_agreement", "the drawn event frequencies must match the enumeration's",
     [("        harm=harm_count / n, attention=att_count / n, false_block=fb_count / n)",
       "        harm=harm_count / n, attention=1.5 * att_count / n, false_block=fb_count / n)")],
     "outside Monte Carlo error", "direct"),

    # ---- the controls ------------------------------------------------------------------------------------
    ("C1_no_gate_baseline", "s=0 must be the no-gate baseline",
     [("                    if esc:\n                        loss += prob * c\n",
       "                    loss += prob * c\n                    if False:\n"),
      (R_AB, "pass"), (R_MISS, "pass"), (R_BIAS, "pass"), (R_FREQ, "pass")],
     "is not the no-gate baseline", "CARVED (the same defect breaks the closure and the frequency read first)"),

    ("C1_interval_arm", "the drawn baseline must sit inside its own interval",
     [NARROW, (R_MISS, "pass"), (R_BIAS, "pass")],
     "the no-gate baseline left the drawn interval", "CARVED (the closure's coverage alarm goes first)"),

    ("C2_useless_reviewer", "a=0,f=0,s=1 must be pi*L + c",
     [("                    if esc:\n                        loss += prob * c\n                        attention += prob",
       "                    if esc:\n                        loss += 2.0 * prob * c\n                        attention += prob"),
      (R_AB, "pass"), (R_MISS, "pass"), (R_BIAS, "pass")],
     "is not pi*L + c", "CARVED (the same defect breaks the closure first)"),

    ("C3_determinism", "two draws at one seed must agree bitwise",
     [("    C3b, _, _, _ = simulate(_p(), 0.5, n=50000, seed=99)",
       "    C3b, _, _, _ = simulate(_p(), 0.5, n=50000, seed=98)")],
     "two draws at the same seed differ", "CARVED-by-construction (the second draw's own seed is the object)"),

    ("C4a_inert_at_b1", "the adversary machinery must be inert at b=1",
     [("                p_reject = (a if render_harm else f) if esc else 0.0",
       "                p_reject = ((a if render_harm else f) * (1.5 if variant == \"mismatch\" else 1.0)) if esc else 0.0")],
     "not inert at b=1", "direct"),

    ("C4b_mismatch_gap", "the mismatch arm must fire with the predicted gap",
     [("                elif variant == \"mismatch\":\n                    render_harm = False",
       "                elif variant == \"mismatch\":\n                    render_harm = P_harm")],
     "does not fire with the predicted gap", "direct"),

    ("C4c_eta_owner", "the substitution arm must follow L*(pi + (1-pi)*eta)",
     [("                    loss += prob * (eta * L if substituted else L)", "                    loss += prob * L")],
     "does not follow L*(pi + (1-pi)*eta)", "direct"),

    ("C4c_interval_arm", "the drawn substitution arm must sit inside its interval",
     [NARROW, (R_MISS, "pass"), (R_BIAS, "pass"), (R_C1_EXACT, "pass"), (R_C1_CI, "pass")],
     "missed its interval in", "CARVED (the closure's and C1's coverage alarms have precedence)"),

    ("C5_guard_enumerate_carrier", "the enumeration's guard must refuse a b<1 read",
     [(GUARD_ENUM, GUARD_ENUM.replace("b < 1.0", "b < 0.0"))],
     "the b<1 guard did not fire", "direct (carrier 1 of 2)"),

    ("C5_guard_simulate_carrier", "the drawing route's guard must refuse a b<1 read",
     [(GUARD_SIM, GUARD_SIM.replace("b < 1.0", "b < 0.0"))],
     "the b<1 guard did not fire", "direct (carrier 2 of 2)"),

    ("C6_coverage_alarm", "the coverage alarm must fire when coverage is bad",
     [("        cover += int(CI[0] <= exact3 <= CI[1])", "        cover += int(CI[0] <= exact3 + 0.2 <= CI[1])")],
     "missed its interval in", "direct"),

    ("affine_in_s", "the screening value must be affine in s",
     [("    return params[\"L\"] * params[\"pi\"] - closed_form(params, s)",
       "    return params[\"L\"] * params[\"pi\"] - closed_form(params, s) + 0.01 * s * s")],
     "not affine in s", "direct"),

    ("threshold_needs_a_sign_change", "the a grid must contain a sign change for a* to be read",
     [("    for a in (0.0, 0.2, 0.4, 0.6, 0.8, 1.0):", "    for a in (0.5, 0.6, 0.7, 0.8, 0.9, 1.0):")],
     "never changes sign on the a grid", "direct"),

    ("threshold_bracket", "the grid must bracket the closed-form a*",
     [("    return (c + cb * (1.0 - pi) * f) / (L * pi)", "    return 4.0 * (c + cb * (1.0 - pi) * f) / (L * pi)")],
     "is not inside the grid's sign-change bracket", "direct"),
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
    # the sites this battery claims to cover, counted from the model itself rather than from the case list
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
                                              "carved" if kind.startswith(("CARVED",)) else "direct",
                                              err[:96]))
    print("\n%d/%d alarms fired" % (len(rows) - len(bad), len(rows)))
    print("the model carries %d raise sites; this battery has %d cases (two guard carriers, one case each)"
          % (len(sites), len(CASES)))
    io.open(os.path.join(HERE, "v0_battery.json"), "w").write(json.dumps(
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
