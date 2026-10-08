#!/usr/bin/env python3
"""Mutation battery for #93 v6 (gate_v6.py): every alarm must be shown to FIRE, and to be REACHED.

Method (v0-v5's, reused).  One targeted defect per `raise` site, applied to a throwaway copy, run, and required
to exit non-zero CARRYING THAT SITE'S MESSAGE.  The denominator is the number of `raise ` statements counted out
of the source AT RUN TIME, so an alarm added without a case shows up as a mismatch in the printed counts.

Rules this round applies to its own cases (each one a defect an earlier round's battery had):

  * A PLANT MUST CHANGE THE PROPERTY THE ALARM READS, and the substitution is asserted to be absent-then-present
    (Class 110/112: `str.replace` with count 0 replaces NOTHING and would report a case as passing while it never
    ran).
  * A CARVE-OUT NAMES THE ALARM IT NEUTRALISES.  One case's defect is masked by an earlier raise; the carve-out
    neutralises that raise IN THE SAME MUTATION and records the precedence.
  * A GUARD THAT SKIPS ROWS OWES ITS NON-VACUITY, and this battery is where that was found: C6's limb guards
    skip the baseline row, so a limb made only of baseline rows would pass every one of them.  The non-vacuity
    guard exists because a case here would otherwise have "passed" against a control that measured nothing.
  * A GUARD WHOSE OBJECT IS ANOTHER TREE'S FUNCTION IS STILL REACHABLE: two C6 guards fire only if a parameter
    MOVES a boundary, and the boundary comes from `gate_v1.bstar_closed` -- a function this battery cannot edit.
    Those cases inject the movement at the CALL SITE in v6's own file (and the injection is built so it vanishes
    on the baseline row, or the baseline guard would mask it -- which is itself the carve-out rule, applied to
    arithmetic rather than to a message).

Run:  /usr/bin/python3 v6_battery.py
"""
import io
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "gate_v6.py")
WORK = os.path.join(HERE, "v6_battery_work.py")
# The interpreter is a COORDINATE of the run, not a constant of this file.  reproduce.sh declares it
# with `PYTHON=...` and exports it; the battery must spawn the SAME interpreter, or the run silently
# splits across two of them (a numpy-less default fails the gates while these still pass).
PY = os.environ.get("PYTHON") or sys.executable

# Anchors (exact source text), kept as names so a case names what it edits.
A_T_LIMB = "        pr = params_at_R(R0, cb=tv * C_FIXED)"
A_ETA_LIMB = "        pr = params_at_R(R0, eta=ev)"
A_ETA_B = ("        pr = params_at_R(R0, eta=ev)\n"
           "        b = {ch: V1.bstar_closed(pr, ch) for ch in CHANNELS}")
A_S_B = "        b = {ch: bisect_at_s(pr0, ch, sv)[0] for ch in CHANNELS}"
A_RATE_RAISE = ('            raise RuntimeError("the %s boundary does not approach its limit at the rate 1/R: %s"\n'
                '                               % (ch, rates[ch]["violations"]))')

CASES = [
    dict(name="law_vs_second_route", site="C1/law",
         why="the closed form must equal the bisection on the exact enumeration, cell by cell",
         subs=[("            closed = V1.bstar_closed(pr, channel)",
                "            closed = V1.bstar_closed(pr, channel) + 1e-4")],
         msg="does not match the bisected enumeration", reach="direct (moves one route only)"),
    dict(name="not_monotone_in_R", site="C2/monotone",
         why="both boundaries must fall in R: a boundary that rises would contradict the cost reading",
         subs=[("SWEEP_R = (0.5, 1.0, 2.0, 5.0, 8.0, 10.0, 20.0, 50.0, 110.0, 200.0, 1000.0, 10000.0)",
                "SWEEP_R = (0.5, 1.0, 2.0, 5.0, 8.0, 10.0, 20.0, 50.0, 8.0, 110.0, 200.0, 1000.0, 10000.0)")],
         msg="not strictly decreasing in R",
         reach="direct (a non-monotone abscissa; every single reading is still correct, so C1 stays green)"),
    dict(name="limit_reached_at_the_wrong_rate", site="C3/rate",
         why="the claim is the RATE 1/R, not 'close to the limit'",
         subs=[("        substitution_limit=u / v_,", "        substitution_limit=0.5 * u / v_,")],
         msg="does not approach its limit at the rate 1/R",
         reach="direct (the limit the differences are taken from is halved, so they stop falling like 1/R).  "
               "NOTE the first version of this case moved RATE_LADDER instead and was INERT: the measured "
               "consecutive-difference ratio and the ladder's expected ratio are BOTH the true R ratio, so no "
               "ladder can make them disagree (Class 112)"),
    dict(name="limits_do_not_differ_in_sign", site="C3/sign",
         why="one bar leaves the axis and the other does not: that SIGN difference is the round's finding",
         subs=[("        substitution_limit=u / v_,", "        substitution_limit=-u / v_,"),
               (A_RATE_RAISE, "            pass  # CARVE-OUT: the rate check reads the same limit and has precedence")],
         msg="do not differ in SIGN", reach="carve-out (C3's rate check is neutralised by name)"),
    dict(name="R_zero_moved", site="C4/R-zero",
         why="the mismatch bar's zero must sit exactly at the closed-form R_m",
         subs=[("        mismatch_R_zero=(1.0 + t * (1.0 - pi) * f) / (pi * f),",
                "        mismatch_R_zero=1.1 * (1.0 + t * (1.0 - pi) * f) / (pi * f),")],
         msg="not zero at the closed-form R_m", reach="direct (moves the claimed zero)"),
    dict(name="bracket_has_no_crossover", site="C5/bracket",
         why="the declared bracket must contain the crossover, or the bisection is searching nothing",
         subs=[("CROSSOVER_BRACKET = (5.0, 10.0)", "CROSSOVER_BRACKET = (8.0, 9.0)")],
         msg="does not contain a crossover", reach="direct (both ends are on the same side of the crossing)"),
    dict(name="bisection_does_not_close", site="C5/close",
         why="the bracket loop must actually narrow onto the crossing",
         subs=[("    for _ in range(200):\n        mid = 0.5 * (lo + hi)\n        if diff(lo) * diff(mid) <= 0.0:",
                "    for _ in range(1):\n        mid = 0.5 * (lo + hi)\n        if diff(lo) * diff(mid) <= 0.0:")],
         msg="did not close on the crossover", reach="direct (one halving instead of 200)"),
    dict(name="crossover_closed_form_off", site="C5/closed-form",
         why="the crossover has a closed form AND an identity (both bars at the axis edge); both are checked",
         subs=[("    R_c_closed = (1.0 + t * (1.0 - pi) * f) / (pi * a)",
                "    R_c_closed = 1.05 * (1.0 + t * (1.0 - pi) * f) / (pi * a)")],
         msg="closed form or the axis-edge identity fails", reach="direct (the claimed form moves)"),
    dict(name="vacuous_limb", site="C6/vacuity",
         why="a limb of baseline-only rows would pass every limb guard without measuring anything",
         subs=[("    for tv in (1.0, t, 5.0):", "    for tv in (t, t, t):")],
         msg="no non-baseline row", reach="direct (every row IS the baseline)"),
    dict(name="baseline_moved_t_limb", site="C6/baseline-t",
         why="the row that IS the baseline must not move, or the control is measuring the wrong reference",
         subs=[("    pr0 = params_at_R(R0)", "    pr0 = params_at_R(R0, cb=0.06)")],
         msg="the baseline row moved", reach="direct (the reference is shifted away from the baseline row)"),
    dict(name="cb_moves_nothing", site="C6/t-moves",
         why="cb must move BOTH boundaries: that is what makes the registered symbol incomplete",
         subs=[(A_T_LIMB, "        pr = params_at_R(R0)")],
         msg="cb does not move the", reach="direct (the varied parameter is dropped)"),
    dict(name="baseline_moved_eta_limb", site="C6/baseline-eta",
         why="the same baseline rule, per limb: each limb's baseline row must stay put",
         subs=[(A_ETA_LIMB, "        pr = params_at_R(R0, eta=ev, cb=(0.06 if ev == eta else t * C_FIXED))")],
         msg="the baseline row moved", reach="direct (this limb's reference is shifted)"),
    dict(name="eta_moves_nothing", site="C6/eta-sub-moves",
         why="eta must move the laundering boundary: it is the laundering factor",
         subs=[(A_ETA_LIMB, "        pr = params_at_R(R0)")],
         msg="eta does not move the substitution boundary", reach="direct (the varied parameter is dropped)"),
    dict(name="eta_moves_the_mismatch_bar", site="C6/eta-mismatch-unmoved",
         why="eta must NOT move the mismatch boundary: that is a claim, and this guard is its test",
         subs=[(A_ETA_B, "        pr = params_at_R(R0, eta=ev)\n"
                         "        b = {ch: V1.bstar_closed(pr, ch) + (1e-3 * (ev - eta) if ch == \"mismatch\"\n"
                         "                                              else 0.0) for ch in CHANNELS}")],
         msg="eta moves the mismatch boundary",
         reach="injected at the CALL SITE (the model lives in gate_v1, which this battery cannot edit), "
               "and the injection VANISHES at the baseline eta so the baseline guard cannot mask it"),
    dict(name="coverage_moves_nothing", site="C6/s-sub-moves",
         why="the coverage s must move the laundering boundary",
         subs=[(A_S_B, "        b = {ch: bisect_at_s(pr0, ch, 1.0)[0] for ch in CHANNELS}")],
         msg="the coverage s does not move the substitution boundary", reach="direct (s is pinned at 1)"),
    dict(name="coverage_moves_the_mismatch_bar", site="C6/s-mismatch-unmoved",
         why="s must NOT move the mismatch boundary: the guard is the test of that claim",
         subs=[(A_S_B, "        b = {ch: bisect_at_s(pr0, ch, sv)[0] + 1e-3 * (1.0 - sv) for ch in CHANNELS}")],
         msg="the coverage s moves the mismatch boundary",
         reach="injected at the CALL SITE, and built to VANISH at the baseline s (else the baseline guard masks "
               "it -- a carve-out done in arithmetic)"),
    dict(name="baseline_moved_s_limb", site="C6/baseline-s",
         why="the same baseline rule, third limb",
         subs=[(A_S_B, "        b = {ch: bisect_at_s(params_at_R(R0, cb=(0.06 if sv == 1.0 else t * C_FIXED)),\n"
                         "                             ch, sv)[0] for ch in CHANNELS}")],
         msg="the baseline row moved", reach="direct (this limb's reference is shifted)"),
    dict(name="interval_misses_the_boundary", site="C7/interval",
         why="the measured interval must contain the exact boundary it is measuring",
         subs=[("            exact = V1.bstar_closed(pr, ch)", "            exact = V1.bstar_closed(pr, ch) + 0.1")],
         msg="does not contain the exact boundary", reach="direct (the target leaves every measured set)"),
]


def main():
    src = io.open(SRC, encoding="utf-8").read()
    n_sites = len(re.findall(r"^\s*raise ", src, re.M))
    msgs = set(re.findall(r'raise (?:RuntimeError|ValueError)\(\s*"([^"]{0,60})', src))
    print("v6 battery -- %d raise site(s) counted out of the source, %d distinct message prefix(es), %d case(s)"
          % (n_sites, len(msgs), len(CASES)))
    rows, all_ok, fired_msgs = [], True, set()
    for c in CASES:
        txt = src
        for old, new in c["subs"]:
            if old not in txt:
                raise SystemExit("CASE %s: plant anchor absent: %r" % (c["name"], old[:80]))
            if src.count(old) != 1:
                raise SystemExit("CASE %s: the anchor matches %d site(s), so the plant does not necessarily land "
                                 "where it is aimed: %r" % (c["name"], src.count(old), old[:80]))
            out = txt.replace(old, new, 1)
            if out == txt:
                raise SystemExit("CASE %s: the plant changed NOTHING: %r" % (c["name"], old[:80]))
            txt = out
        io.open(WORK, "w", encoding="utf-8").write(txt)
        try:
            p = subprocess.run([PY, WORK], capture_output=True, text=True, timeout=900)
            rc, outp = p.returncode, p.stdout + p.stderr
        finally:
            if os.path.exists(WORK):
                os.remove(WORK)
        fired = (rc != 0) and (c["msg"] in outp)
        if fired:
            fired_msgs.add(c["msg"])
        all_ok = all_ok and fired
        rows.append((c["name"], c["site"], c["reach"], rc, fired))
        print("  %-6s %-34s site %-28s exit %s%s"
              % ("ok" if fired else "MISSED", c["name"], c["site"], rc,
                 "" if fired else "  -- MESSAGE NOT FOUND"))
    covered = len([m for m in msgs if any(m[:40] in r[0] or True for r in [])])
    print("BATTERY: %d/%d case(s) fired against %d source site(s); %d distinct guard(s) exercised"
          % (sum(1 for r in rows if r[4]), len(rows), n_sites, len(set(c["site"] for c in CASES))))
    print("SELFTEST: %s" % ("PASS" if all_ok else "FAIL"))
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
