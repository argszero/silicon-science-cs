#!/usr/bin/env python3
"""Mutation battery for #93 v5 (gate_v5.py): every alarm must be shown to FIRE, and to be REACHED.

Method (v0-v4's, reused and tightened).  One targeted defect per `raise` site, applied to a throwaway copy, run,
and required to exit non-zero CARRYING THAT SITE'S MESSAGE.  The denominator is counted out of the source at run
time (`raise ` occurrences), so an alarm added without a case shows up as a mismatch in the printed counts.

Three rules this round applies to its own cases, each of them a defect an earlier round's battery had:

  * A PLANT MUST CHANGE THE PROPERTY THE ALARM READS (Class 110/112).  Every substitution is asserted to be
    present in the source AND (#) to change it -- `str.replace` with count 0 replaces NOTHING and would report a
    case as passing while it never ran, so the applied text is compared before the run.
  * A CARVE-OUT NAMES THE ALARM IT NEUTRALISES.  One case's defect would be masked by an earlier raise; the
    carve-out neutralises that raise IN THE SAME MUTATION and records which alarm has precedence.
  * AN UNREACHABLE BRANCH OWES A PLANT.  C6 states the theorem that the Fieller set is never EMPTY for an affine
    read, so the `empty` branch cannot be reached through the model.  It is reached here by feeding `fieller` a
    NEGATIVE leading coefficient directly (a crafted input, not a mutated run): a branch nobody can fire is
    decoration, whatever the reason it cannot fire.

Run:  /usr/bin/python3 v5_battery.py
"""
import io
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "gate_v5.py")
WORK = os.path.join(HERE, "v5_battery_work.py")
PY = "/usr/bin/python3"

# The probe plants (sites 3-6) are call sites appended to main: the wls guards are internal, so the only honest
# way to reach them is to CALL them with the input that violates their precondition.
PROBE = '    __import__("sys").stdout.flush()\n'

CASES = [
    dict(name="unknown_channel", site="defect_for/unknown",
         why="a channel with no defect map must not be silently drawn as if it had one",
         subs=[('CHANNELS = ("mismatch", "substitution", "none")',
                'CHANNELS = ("mismatch", "substitution", "bogus")')],
         msg="unknown channel", reach="direct"),
    dict(name="no_gate_design", site="draw_curve/per-is-None",
         why="the no-gate design has no gate to read a boundary from; its `per` is None by contract",
         subs=[('DESIGN = "D1"', 'DESIGN = "D0"')],
         msg="the no-gate design cannot read a boundary", reach="direct"),
    dict(name="negative_standard_error", site="wls/negative-se",
         why="a standard error is a square root; a negative one cannot come from a sample",
         subs=[('    res["checks"] = dict(', PROBE + '    wls([0.0, 1.0], [1.0, 2.0], [-0.1, 0.1])\n'
                                             '    res["checks"] = dict(')],
         msg="a negative standard error cannot come from a sample", reach="probe"),
    dict(name="over_determined_line", site="wls/more-than-two-exact",
         why="three exact fidelities determine a line twice over; fitting it would hide a contradiction",
         subs=[('    res["checks"] = dict(',
                PROBE + '    wls([0.0, 0.5, 1.0], [1.0, 3.0, 5.0], [0.0, 0.0, 0.0])\n'
                        '    res["checks"] = dict(')],
         msg="more than two exact fidelities", reach="probe"),
    dict(name="contradicts_the_exact_line", site="wls/inexact-contradicts-exact",
         why="a noisy point far off the line the exact fidelities fix is a defect of the model, not noise",
         subs=[('    res["checks"] = dict(',
                PROBE + '    wls([0.0, 0.5, 1.0], [1.0, 9.0, 5.0], [0.0, 0.1, 0.0])\n'
                        '    res["checks"] = dict(')],
         msg="contradicts the two exact fidelities", reach="probe"),
    dict(name="slope_not_determined", site="wls/one-exact-too-few",
         why="one exact point and one noisy point leave the slope undetermined; a fit would invent it",
         subs=[('    res["checks"] = dict(',
                PROBE + '    wls([0.0, 1.0], [1.0, 2.0], [0.0, 0.1])\n    res["checks"] = dict(')],
         msg="the slope is not determined", reach="probe"),
    dict(name="mapping_is_wrong", site="C1/mapping",
         why="the preimage of the registered fidelity must reproduce the registered variant, not merely a defect",
         subs=[('        return dict(delta=1.0 - b, sigma_v=0.0, sigma_i=0.0)',
                '        return dict(delta=b, sigma_v=0.0, sigma_i=0.0)')],
         msg="the b -> defect mapping does not reproduce", reach="direct (flips the rendering defect)"),
    dict(name="estimator_off_the_model", site="C2/estimator",
         why="the estimator must recover the model's own boundary, not merely a stable number",
         subs=[('                b_hat_star=(-a_hat / b_hat) if b_hat != 0.0 else None,',
                '                b_hat_star=((-a_hat / b_hat) + 5.0) if b_hat != 0.0 else None,')],
         msg="the estimator does not recover the exact boundary", reach="direct (moves the estimate)"),
    dict(name="bootstrap_reads_the_loss", site="C3/two-routes",
         why="the bootstrap must resample the SAME quantity the point fit reads (the value, not the loss); this "
             "is the defect the round actually hit, and only the two-route comparison can see it",
         subs=[('            v.append(e0 - float(s.mean()))', '            v.append(float(s.mean()))')],
         msg="the Fieller set disagree", reach="direct (the real dev-time defect)"),
    dict(name="endpoints_off_the_definition", site="C4/defining-property",
         why="the set's endpoints must BE the fidelities where |value| = z*SE, not merely near them",
         subs=[('    base.update(kind="bounded", lo=lo, hi=hi, width=hi - lo, clips=bool(lo < 0.0 or hi > 1.0))',
                '    lo, hi = lo - 0.2, hi + 0.2\n'
                '    base.update(kind="bounded", lo=lo, hi=hi, width=hi - lo, clips=bool(lo < 0.0 or hi > 1.0))')],
         msg="defining property", reach="direct (moves both endpoints off the definition)"),
    dict(name="precision_law_off", site="C4/precision-law",
         why="the precision law must predict the width the interval actually has, inside its derived regime",
         subs=[('        predicted = 2.0 * Z * se_of_line(cov, r["b_hat_star"]) / abs(b_hat)',
                '        predicted = 4.0 * Z * se_of_line(cov, r["b_hat_star"]) / abs(b_hat)')],
         msg="precision law", reach="direct (doubles the law's prediction, endpoints untouched)"),
    dict(name="width_does_not_scale", site="C5/scaling",
         why="the width must fall as 1/sqrt(n); a width that does not move with n is not a sampling uncertainty",
         subs=[('            w[n] = f.get("width") if f["kind"] == "bounded" else None',
                '            w[n] = 1.0')],
         msg="does not scale as 1/sqrt(n)", reach="direct (the ratio becomes 1.0 against an expected 2.0)"),
    dict(name="the_null_stops_being_a_null", site="C6/null-size",
         why="the `none` channel's defect must not depend on b, or it is not a null for the slope test",
         subs=[('        return dict(delta=0.0, sigma_v=0.0, sigma_i=0.0)',
                '        return dict(delta=1.0 - b, sigma_v=0.0, sigma_i=0.0)')],
         msg="the states or the slope test's own size", reach="direct (gives the null a real slope)"),
    dict(name="coverage_below_nominal", site="C7/calibration",
         why="the interval must cover the exact boundary at the rate it claims; a target shifted off every "
             "interval is the cleanest way to break coverage and nothing else",
         subs=[('    exact = None if channel == "none" else V1.bstar_closed(params, channel)',
                '    exact = None if channel == "none" else V1.bstar_closed(params, channel) + 0.45'),
               # CARVE-OUT: C2 reads the same shifted target and would raise FIRST, masking C7's alarm.  The
               # carve-out neutralises C2's raise in the SAME mutation and records the precedence.
               ('        raise RuntimeError("the estimator does not recover the exact boundary: worst dev %s over %d reading(s)"\n'
                '                           % (worst_dev, len(in_axis)))',
                '        pass  # CARVE-OUT: C2 reads the same shifted target and would mask C7')],
         msg="coverage is not consistent with the nominal",
         reach="direct + carve-out (C2 has precedence and is neutralised by name)"),
]


def main():
    src = io.open(SRC, encoding="utf-8").read()
    sites = re.findall(r"^\s*raise [A-Za-z]+Err?o?r?o?r?\(", src, re.M)
    n_sites = len(re.findall(r"^\s*raise ", src, re.M))
    print("v5 battery -- %d raise site(s) counted out of the source, %d case(s)" % (n_sites, len(CASES)))
    covered = sorted(set(c["site"].split("/")[-1] for c in CASES))
    rows, all_ok = [], True
    for c in CASES:
        txt = src
        for old, new in c["subs"]:
            if old not in txt:
                raise SystemExit("CASE %s: plant anchor absent: %r" % (c["name"], old[:70]))
            out = txt.replace(old, new, 1)
            if out == txt:                      # Class 112: a replacement that changes nothing proves nothing
                raise SystemExit("CASE %s: the plant changed NOTHING: %r" % (c["name"], old[:70]))
            txt = out
        io.open(WORK, "w", encoding="utf-8").write(txt)
        try:
            p = subprocess.run([PY, WORK], capture_output=True, text=True, timeout=900)
            rc, outp = p.returncode, p.stdout + p.stderr
        finally:
            if os.path.exists(WORK):
                os.remove(WORK)
        fired = (rc != 0) and (c["msg"] in outp)
        all_ok = all_ok and fired
        rows.append((c["name"], c["site"], c["reach"], rc, fired))
        print("  %-6s %-30s site %-28s exit %s %s"
              % ("ok" if fired else "MISSED", c["name"], c["site"], rc, "" if fired else "-- MESSAGE NOT FOUND"))
    # The guards whose precondition no WHOLE RUN can violate: `fieller`'s negative-discriminant guard is reached
    # by handing it a matrix that is not a covariance.  (The first version of this case tried to reach an EMPTY
    # STATE through the model and could not -- because an affine read's set always contains its crossing.  The
    # branch was then removed and turned into this guard, which is the honest form: a precondition, not a state.)
    sys.path.insert(0, HERE)
    import numpy as np
    import gate_v5 as V5
    crafted_ok = True
    try:
        V5.fieller(3.0, 1.0, np.array([[1.0, 0.9], [0.9, 0.01]]))   # 0.81 > 0.01: not a covariance
        got = "no raise"
    except RuntimeError as exc:
        got = str(exc)
    crafted_ok = "a negative discriminant means the matrix is not a covariance" in got
    all_ok = all_ok and crafted_ok
    print("  %-6s %-30s site %-28s %s"
          % ("ok" if crafted_ok else "MISSED", "covariance_guard", "fieller/negative-disc",
             "raised" if crafted_ok else got[:60]))
    # and the constructive companion: the crossing lies inside its own set (the theorem C4d asserts)
    inside_ok = True
    try:
        s = V5.fieller(0.5, 1.0, np.array([[0.01, 0.0], [0.0, 0.01]]))
        inside_ok = s["kind"] == "bounded" and s["lo"] <= -0.5 / 1.0 <= s["hi"]
    except RuntimeError:
        inside_ok = False
    all_ok = all_ok and inside_ok
    print("  %-6s %-30s site %-28s %s"
          % ("ok" if inside_ok else "MISSED", "crossing_is_inside_its_set", "C4d/containment",
             "b* in [lo, hi]" if inside_ok else "NOT CONTAINED"))
    covered = sorted(set(covered) | {"negative-disc", "containment"})
    print("BATTERY: %d/%d case(s) fired; %d site(s) covered (%s)"
          % (sum(1 for r in rows if r[4]), len(rows), len(covered), ", ".join(covered)))
    print("SELFTEST: %s" % ("PASS" if all_ok else "FAIL"))
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
