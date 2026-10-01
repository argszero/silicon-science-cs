#!/usr/bin/env python3
"""#93 R418 -- v4: the AXIS-SENSITIVITY ratio, the registration's success metric (b), which had no owner.

Why this instrument exists.  The registration names five success metrics; metric (b) is

    (dE / da) / (dE / db)   at  b in {0, 0.5, 1}

and PB2 is registered **against this quantity**: "the marginal reduction in expected harm from one unit of
reviewer accuracy at fixed coverage exceeds the marginal reduction from the same unit of binding fidelity, at
every fidelity level" -- i.e. the ratio exceeds 1 at every b.  The registered opposite direction is that
fidelity pays more and the gap widens as b falls (ratio < 1, decreasing in b).

Reading the record in R417 found that **no instrument computed it**: v0 read the screening closure, v1 the map
and its `b*`, v2 the design ladder, v3 the sampling route, and a note counted PB2 as "read on its own
instrument" because its *screening* clause had been.  A prior's outcome cannot be written from a derivation,
so this round gives the metric an instrument.

STRUCTURE (and why it is split this way).  Measurement and checking are separate: `measure` reads the numbers
and the nine `chk_*` functions each take the object they are about and raise on failure.  That is what makes
each alarm independently reachable -- the battery in `v4_battery.py` feeds each check a crafted input, rather
than re-running the whole instrument and hoping the alarm it wants is the first one to fire (this round's first
battery had 12 cases and caught 4, because almost every perturbation tripped an earlier check).

WHAT IS MEASURED, AND WITH WHAT
  E             the expected loss per action UNDER THE GATE at the coverage the registration fixes for the
                comparison (s = 1, PB3's own "escalate every action" rule), read from v0's exact enumeration
                (`screen_only=False`) -- never from a closed form.
  dE/da, dE/db  differences of that enumeration.  Central where it fits; **forward at the lower end of the
                axis and backward at the upper end**, because the registered fidelities INCLUDE both ends (0
                and 1) and a central difference would step outside the unit interval there.  Step h = 1e-4,
                declared; `chk_B` shows the read does not depend on it, `chk_B2` that the boundary rule and the
                central rule are one derivative read two ways.
  ratio         (dE/da) / (dE/db).  The registered wording gives no sign, so the instrument reports the raw
                ratio and ASSERTS (`chk_D`) that both derivatives are <= 0, which is what makes the raw ratio
                equal the ratio of magnitudes.  A vanishing derivative is classified, never divided through.
  crossover     the b at which the ratio reaches 1 (bisection on the MEASURED ratio), against the closed form's
                prediction.

A ZERO TEST MUST BE RELATIVE.  The first version tested zeros with an absolute threshold and reported a ratio
of 5.76e12 for the axisless variant at b = 0.5 -- the quotient of a real derivative by the floating-point zero
3.47e-14.  The threshold is now relative to the cell's own scale, and which variants HAVE a fidelity axis is
DECLARED from the model (`DECLARED_B_AXIS`) and verified two-sided (`chk_A2`).

Run:  python3 gate_v4.py            (report + gate_v4_results.json)
"""
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import gate_v0 as V0                                                          # noqa: E402
import gate_v1 as V1                                                          # noqa: E402

OUT = os.path.join(HERE, "gate_v4_results.json")
DEFAULT = dict(V0.DEFAULT)
H = 1e-4                       # the declared difference step
VARIANTS = ("none", "mismatch", "substitution")
B_READ = (0.0, 0.5, 1.0)       # the fidelities the registration names
TOL = 1e-9
NOISE = 1e-10                  # relative to max(|dE/da|, |dE/db|, 1.0) in the same cell
STEPS = (1e-2, 1e-3, 1e-4, 1e-5)
# Which variants HAVE a fidelity axis -- declared from the model, not inferred from a number: `none` ignores b
# entirely, so dE/db is zero BY CONSTRUCTION there.  chk_A2 verifies the declaration both ways.
DECLARED_B_AXIS = {"none": False, "mismatch": True, "substitution": True}

LOG = []


def say(*a):
    line = " ".join(str(x) for x in a)
    LOG.append(line)
    print(line, flush=True)


# --------------------------------------------------------------------------- measurement
def loss_gated(params, variant, b, s=1.0):
    """E, the expected loss per action under the gate, at coverage s.  From the exact enumeration."""
    return V0.enumerate_exact(params, s, variant=variant, b=b, screen_only=False)[0]


def side_for(b, h=None):
    """The declared boundary rule.  The fidelities the registration names include BOTH ends of the axis, where
    a central difference would step outside the unit interval."""
    h = H if h is None else h
    if b < h:
        return "forward"
    if b > 1.0 - h:
        return "backward"
    return "central"


def dloss(params, variant, b, which, h=None, side=None):
    """A difference of E in `a` or `b`: a parameter grid step, not a fitted slope.  The bounds guard reads the
    points the CHOSEN rule evaluates and nothing else -- guarding a point the rule does not use is how a
    forward difference at b = 0 was refused for a step it never takes."""
    h = H if h is None else h
    side = side or side_for(b, h)
    if which == "a":
        up, dn = V1._p(**dict(params, a=params["a"] + h)), V1._p(**dict(params, a=params["a"] - h))
        need = [up["a"], dn["a"]] if side == "central" else ([up["a"]] if side == "forward" else [dn["a"]])
        if not all(0.0 <= x <= 1.0 for x in need):
            raise RuntimeError("dE/da step leaves (0,1): a=%r h=%r side=%s" % (params["a"], h, side))
    else:
        up, dn = dict(params, b=params["b"] + h), dict(params, b=params["b"] - h)
        need = [up["b"], dn["b"]] if side == "central" else ([up["b"]] if side == "forward" else [dn["b"]])
        if not all(0.0 <= x <= 1.0 for x in need):
            raise RuntimeError("dE/db step leaves (0,1): b=%r h=%r side=%s" % (params["b"], h, side))
    if side == "central":
        return (loss_gated(up, variant, up["b"]) - loss_gated(dn, variant, dn["b"])) / (2.0 * h)
    if side == "forward":
        return (loss_gated(up, variant, up["b"]) - loss_gated(params, variant, b)) / h
    return (loss_gated(params, variant, b) - loss_gated(dn, variant, dn["b"])) / h


def measure_ratio(params, variant, b, h=None):
    """The cell: both derivatives and the ratio, with a vanishing derivative CLASSIFIED, never divided."""
    h = H if h is None else h
    p = V1._p(**dict(params, b=b))
    da = dloss(p, variant, b, "a", h)
    db = dloss(p, variant, b, "b", h)
    scale = max(abs(da), abs(db), 1.0)
    if da > NOISE * scale or db > NOISE * scale:
        raise RuntimeError("E is non-decreasing in a or b at (%s, b=%r): dE/da=%.3e dE/db=%.3e"
                           % (variant, b, da, db))
    base = dict(variant=variant, b=b, dE_da=da, dE_db=db, side=side_for(b, h))
    if abs(db) <= NOISE * scale:
        return dict(base, ratio=None, axis=DECLARED_B_AXIS[variant],
                    status="NO b-AXIS: E is constant in fidelity, so this axis has no statistic")
    if abs(da) <= NOISE * scale:
        return dict(base, ratio=0.0, axis=True,
                    status="ACCURACY IS INERT: the reviewer's decision cannot reach the executed object")
    return dict(base, ratio=da / db, axis=True, status="ok")


def predict_ratio(params, variant, b, s=1.0):
    """The closed form, from v1's slope laws (V = base + slope(b)*s and E = E0 - V): the PREDICTION."""
    pi, a, f = params["pi"], params["a"], params["f"]
    L, cb = params["L"], params["cb"]
    eta = params["eta"]
    if variant == "none":
        return None, None
    num = s * L * pi * b
    if variant == "mismatch":
        return num, num / (s * L * pi * (a - f))
    return num, num / (s * (L * pi * a - cb * (1.0 - pi) * f) + eta * L * (1.0 - pi))


def predict_crossover(params, variant, s=1.0):
    """The b at which the ratio reaches 1: mismatch -> a - f; substitution -> den / (s L pi)."""
    pi, a, f = params["pi"], params["a"], params["f"]
    L, cb = params["L"], params["cb"]
    eta = params["eta"]
    if variant == "mismatch":
        return a - f
    return (s * (L * pi * a - cb * (1.0 - pi) * f) + eta * L * (1.0 - pi)) / (s * L * pi)


def bisect_crossover(params, variant, lo=0.0, hi=1.0, steps=60):
    """Locate ratio = 1 on the MEASURED read; None if the ratio stays on one side of 1."""
    def g(b):
        r = measure_ratio(params, variant, b)["ratio"]
        return None if r is None else r - 1.0

    g0, g1 = g(lo), g(hi)
    if g0 is None or g1 is None or (g0 > 0) == (g1 > 0):
        return None
    for _ in range(steps):
        mid = 0.5 * (lo + hi)
        gm = g(mid)
        if gm is None:
            return None
        if (gm > 0) == (g0 > 0):
            lo, g0 = mid, gm
        else:
            hi = mid
    return 0.5 * (lo + hi)


def measure(params):
    """Every number the checks read.  No check raises in here."""
    rows = []
    for variant in VARIANTS:
        for b in B_READ:
            m = measure_ratio(params, variant, b)
            _num, pred = predict_ratio(params, variant, b)
            m["predicted_ratio"] = pred
            m["deviation"] = None if (pred is None or m["ratio"] is None) else abs(m["ratio"] - pred)
            rows.append(m)
    spread = {}
    for variant in ("mismatch", "substitution"):
        vals = [measure_ratio(params, variant, 0.5, h=h)["ratio"] for h in STEPS]
        spread[variant] = dict(h=list(STEPS), ratios=vals,
                               relative_spread=(max(vals) - min(vals)) / abs(vals[0]))
    b2 = {}
    for variant in ("mismatch", "substitution"):
        p5 = V1._p(**dict(params, b=0.5))
        cen = dloss(p5, variant, 0.5, "b", H, side="central")
        fwd = dloss(p5, variant, 0.5, "b", H, side="forward")
        b2[variant] = dict(central=cen, forward=fwd, relative=abs(cen - fwd) / abs(cen))
    devs = []
    for variant in VARIANTS:
        for b in B_READ:
            p = V1._p(**dict(params, b=b))
            devs.append(abs((params["L"] * params["pi"] - loss_gated(p, variant, b))
                            - V1.value_closed(p, variant, b, 1.0)))
    p0 = V1._p(**dict(params, eta=0.0))
    eta0 = dict(measured={v: measure_ratio(p0, v, 0.5)["ratio"] for v in ("mismatch", "substitution")})
    pi, a, f = params["pi"], params["a"], params["f"]
    L, cb = params["L"], params["cb"]
    eta0["denominators"] = dict(mismatch=L * pi * (a - f), substitution=L * pi * a - cb * (1.0 - pi) * f)
    eta0["predicted"] = {v: 0.5 * L * pi / eta0["denominators"][v] for v in eta0["denominators"]}
    cross = {v: dict(numeric=bisect_crossover(params, v), predicted=predict_crossover(params, v))
             for v in ("mismatch", "substitution")}
    for v in cross:
        cross[v]["inside_unit_interval"] = cross[v]["predicted"] <= 1.0
        cross[v]["deviation"] = (None if cross[v]["numeric"] is None
                                 else abs(cross[v]["numeric"] - cross[v]["predicted"]))
    return dict(rows=rows, spread=spread, b2=b2, devs=devs, eta0=eta0, cross=cross)


# --------------------------------------------------------------------------- the checks, each on its own object
def chk_A1(rows):
    """The measured ratio must reproduce the closed form wherever both exist."""
    dev = [r["deviation"] for r in rows if r["deviation"] is not None]
    worst = max(dev) if dev else None
    if worst is None or worst >= TOL:
        raise RuntimeError("A1 FAILED: numeric ratio does not reproduce the closed form (worst %r)" % worst)
    return dict(id="A1-numeric-vs-closed", readings=len(dev), worst=worst, ok=True)


def chk_A2(rows):
    """The axis the MODEL declares and the axis the READING shows must agree, variant by variant."""
    byv = {}
    for r in rows:
        byv.setdefault(r["variant"], []).append(r)
    per = {v: dict(declared=DECLARED_B_AXIS[v], measured_has_axis=all(r["axis"] for r in rs),
                   rows=len(rs), ratios=[r["ratio"] for r in rs]) for v, rs in byv.items()}
    bad = [v for v, d in per.items() if d["declared"] != d["measured_has_axis"]]
    if bad:
        raise RuntimeError("A2 FAILED: a variant's declared axis and its measured axis disagree: %r" % per)
    return dict(id="A2-declared-vs-measured-axis", per_variant=per, ok=True)


def chk_A3(rows):
    """At zero fidelity reviewer accuracy is EXACTLY inert: the executed object ignores the decision."""
    z = [r for r in rows if r["b"] == 0.0 and r["variant"] != "none"]
    ok = bool(z) and all(r["ratio"] == 0.0 and "INERT" in r["status"] for r in z)
    if not ok:
        raise RuntimeError("A3 FAILED: at b = 0 reviewer accuracy is not exactly inert")
    return dict(id="A3-zero-fidelity-inert", rows=len(z), ok=True)


def chk_B(spread):
    """The read must not move with the step: the ratio is a property of the model, not of h."""
    worst = max(v["relative_spread"] for v in spread.values())
    if worst >= 1e-6:
        raise RuntimeError("B FAILED: the ratio moves with the step (worst relative spread %.3e)" % worst)
    return dict(id="B-step-independence", spread=spread, worst=worst, ok=True)


def chk_B2(b2):
    """The boundary rule and the central rule are ONE derivative read two ways.

    Reach, stated because it is narrower than the name: on a model AFFINE in b the two rules agree exactly, so
    this check sees a rule that reads a DIFFERENT POINT or a different function, not a truncation error."""
    worst = max(v["relative"] for v in b2.values())
    if worst >= 1e-3:
        raise RuntimeError("B2 FAILED: the boundary rule and the central rule disagree (%.3e)" % worst)
    return dict(id="B2-boundary-rule", readings=b2, worst=worst, ok=True)


def chk_C(devs):
    """The v4 route is the same model as v1: the value read both ways must agree."""
    worst = max(devs) if devs else None
    if worst is None or worst >= 1e-12:
        raise RuntimeError("C FAILED: the v4 route and v1's closed form disagree (worst %.3e)" % (worst or -1.0))
    return dict(id="C-same-model", readings=len(devs), worst=worst, ok=True)


def chk_D(rows):
    """Both derivatives <= 0 everywhere, so the raw ratio IS the ratio of magnitudes."""
    off = [r for r in rows if r["dE_da"] > 0 or r["dE_db"] > 0]
    if off:
        raise RuntimeError("D FAILED: a derivative is positive, so the raw ratio is not the magnitude ratio")
    return dict(id="D-sign-convention", readings=len(rows), ok=True)


def chk_E(eta0):
    """With laundering switched off the two channels still differ, by an exact term."""
    ok = all(abs(eta0["measured"][v] - eta0["predicted"][v]) < TOL for v in eta0["measured"])
    ok = ok and eta0["denominators"]["mismatch"] != eta0["denominators"]["substitution"]
    if not ok:
        raise RuntimeError("E FAILED: the eta = 0 channels' ratios do not follow their own denominators")
    return dict(id="E-channel-term", measured=eta0["measured"], predicted=eta0["predicted"],
                denominators=eta0["denominators"], ok=True)


def chk_F(cross, params):
    """The crossover follows its prediction, and a channel whose prediction lies outside the unit interval has
    NO crossover -- stated as a refusal rather than as a missing number."""
    mis = cross["mismatch"]
    ok = (mis["numeric"] is not None and mis["deviation"] is not None and mis["deviation"] < 1e-6
          and cross["substitution"]["numeric"] is None
          and not cross["substitution"]["inside_unit_interval"])
    if not ok:
        raise RuntimeError("F FAILED: the crossover does not follow its prediction (%r)" % cross)
    return dict(id="F-crossover", cross=cross, a_minus_f=params["a"] - params["f"], ok=True)


CHECKS = (chk_A1, chk_A2, chk_A3, chk_B, chk_B2, chk_C, chk_D, chk_E, chk_F)


def main():
    res = dict(round="R418", default=DEFAULT, step=H, coverage=1.0,
               note="metric (b) of the registration: (dE/da)/(dE/db) at b in {0,0.5,1}; E is the expected loss "
                    "under the gate read from v0's exact enumeration; the closed form is the prediction")
    m = measure(DEFAULT)

    say("=== A. the metric at the registered fidelities (E from the exact enumeration)")
    for r in m["rows"]:
        say("  %-13s b=%.2f [%-8s] dE/da=%9.2e  dE/db=%9.2e  ratio=%s  predicted=%s  %s"
            % (r["variant"], r["b"], r["side"], r["dE_da"], r["dE_db"],
               "None" if r["ratio"] is None else "%.6f" % r["ratio"],
               "None" if r["predicted_ratio"] is None else "%.6f" % r["predicted_ratio"], r["status"][:44]))
    checks = []
    for fn in CHECKS:
        arg = {"chk_A1": m["rows"], "chk_A2": m["rows"], "chk_A3": m["rows"], "chk_B": m["spread"],
               "chk_B2": m["b2"], "chk_C": m["devs"], "chk_D": m["rows"], "chk_E": m["eta0"]}[fn.__name__] \
            if fn.__name__ != "chk_F" else (m["cross"], DEFAULT)
        out = fn(*arg) if isinstance(arg, tuple) else fn(arg)
        checks.append(out)
        say("  %-34s PASS  %s" % (out["id"], json.dumps({k: v for k, v in out.items()
                                                         if k not in ("id", "ok")}, sort_keys=True)[:96]))
    res["checks"] = checks

    say("\n=== B/C/D detail")
    say("  step independence: worst relative spread %.2e over %d steps"
        % (max(v["relative_spread"] for v in m["spread"].values()), len(STEPS)))
    say("  boundary rule vs central at b = 0.5: worst relative %.2e"
        % max(v["relative"] for v in m["b2"].values()))
    say("  value read two ways: %d readings, worst difference %.3e" % (len(m["devs"]), max(m["devs"])))
    say("  eta = 0: mismatch ratio %.6f (den %.4f), substitution ratio %.6f (den %.4f)"
        % (m["eta0"]["measured"]["mismatch"], m["eta0"]["denominators"]["mismatch"],
           m["eta0"]["measured"]["substitution"], m["eta0"]["denominators"]["substitution"]))

    say("\n=== F. the crossover: the fidelity at which reviewer accuracy stops paying more than binding")
    for v, c in m["cross"].items():
        say("  %-13s numeric=%-10s predicted=%.6f  %s"
            % (v, "none in [0,1]" if c["numeric"] is None else "%.6f" % c["numeric"], c["predicted"],
               "inside the unit interval" if c["inside_unit_interval"] else
               "OUTSIDE the unit interval -> no crossover exists"))
    say("  the predicted crossover for a misrepresenting channel is a - f = %.6f (the reviewer's own Youden "
        "margin)" % (DEFAULT["a"] - DEFAULT["f"]))

    say("\n=== G. PB2's own verdict: does reviewer accuracy pay more than binding fidelity? (ratio > 1)")
    verdict = {}
    for variant in ("mismatch", "substitution"):
        per = {}
        for b in (0.5, 1.0):
            r = measure_ratio(DEFAULT, variant, b)["ratio"]
            per[b] = dict(ratio=r, accuracy_pays_more=r > 1.0)
        verdict[variant] = per
        say("  %-13s %s" % (variant, {k: ("accuracy pays more (%.4f > 1)" % v["ratio"]) if v["accuracy_pays_more"]
                                      else ("fidelity pays more (%.4f < 1)" % v["ratio"])
                                      for k, v in per.items()}))
    res["pb2_verdict"] = verdict
    res["log"] = LOG
    io.open(OUT, "w", encoding="utf-8").write(json.dumps(res, indent=1, sort_keys=True))
    say("\nwrote %s | checks %d/%d PASS" % (os.path.basename(OUT), len(checks), len(CHECKS)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
