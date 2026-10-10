#!/usr/bin/env python3
"""#93 v2 -- the design axis: is a use-time check an INDEPENDENT repair, or is it bounded by the representation
it reads?  (PB4)

WHAT THIS ROUND ASKS.  The registration's PB4 states the published claim -- "adding a use-time check of the
approved object removes the laundering channel even when the rendering itself is unfaithful, because the check
is independent of the rendering" -- and registers the OPPOSITE direction as its prediction: "the repair is
fidelity-equivalent, not independent: a use-time check that reads the same derived representation as the
rendering restores b only up to the faithfulness of that representation, so its marginal value is itself a
function of b".

THE MODEL (v1's loss / attention / false-block parameters, with the channel split into three defect classes).
What makes a defect invisible to a check is not its size but WHETHER THE REPRESENTATION THE CHECK READS RECORDS
IT:

    delta   display mismatch         the human's rendering differs from the canonical representation R (they
                                     see a benign object).  The check reads R, so it is BLIND to this.  A
                                     canonical rendering removes it.
    sigma_v R-VISIBLE substitution   the executed action differs from the approved one in a way R records.  A
                                     check that compares executed vs approved IN R'S TERMS catches it.
    sigma_i R-INVISIBLE substitution the executed action differs but R does not record the difference (R-equal).
                                     Neither the human (who approves R) nor a same-representation check can see
                                     it.  Only a check that re-derives from the REQUEST can.

DESIGNS (the registration's four, plus the two the question needs):
    D0  no gate                                      the baseline, E = L*pi by definition
    D1  text approval                                exposed to delta, sigma_v, sigma_i; no check
    D2  canonical rendering                          delta removed (the human reads R itself)
    D3  canonical + use-time check reading R          sigma_v caught; delta already gone; sigma_i SURVIVES
    D4  canonical + check re-derived from request     sigma_v and sigma_i caught (the "independent" repair)
    D5  check reading R, WITHOUT canonical rendering  sigma_v caught; delta and sigma_i survive

THE FALSIFIABLE CLAIMS, PRE-REGISTERED BEFORE THE RUN:
  P1  CONTROL: with no defect every design equals v1's b = 1 screening value exactly, and D0 equals L*pi exactly.
  P2  THE CHECK HAS REAL VALUE where the channel is R-visible: V(D3) > V(D2) strictly iff sigma_v > 0, and
      V(D3) = V(D2) exactly when sigma_v = 0 (nothing R-visible to catch).
  P3  THE CHECK IS NOT INDEPENDENT -- its blind spot is exactly sigma_i: V(D4) - V(D3) > 0 strictly iff
      sigma_i > 0, monotone in sigma_i, and zero at sigma_i = 0 (the isolating control).
  P4  THE CHECK DOES NOT REPAIR THE DISPLAY CLASS: V(D3) - V(D5) > 0 strictly iff delta > 0.  FALSIFIER: if the
      gap vanishes at delta > 0, the check repairs a class it cannot read and this model is wrong.
  P5  DESIGN ORDERING (the registration's external-validation arm): D0 worst, D1 <= D2 <= D3 <= D4, and the
      published ordering "the VAC arm beats the text-approval arm, the unbound arm is worst" holds.
  P6  THE PUBLISHED ANCHOR IS REACHABLE: with the substitution channel closed the attack success is exactly 0
      (2609.18411's "0% with binding"), and with the channel open it is higher at every design.

Run:  /usr/bin/python3 gate_v2.py      (writes gate_v2_results.json beside itself)
"""
import io
import json
import math
import os
import sys
import zlib

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
OUT = os.path.join(HERE, "gate_v2_results.json")

import gate_v0 as V0                        # noqa: E402
import gate_v1 as V1                        # noqa: E402

DESIGNS = ("D0", "D1", "D2", "D3", "D4", "D5")
DESIGN_SPEC = {
    "D0": dict(gate=False, canonical=False, check=False),
    "D1": dict(gate=True, canonical=False, check=False),
    "D2": dict(gate=True, canonical=True, check=False),
    "D3": dict(gate=True, canonical=True, check="R"),
    "D4": dict(gate=True, canonical=True, check="request"),
    "D5": dict(gate=True, canonical=False, check="R"),
}
DEFECT = dict(delta=0.30, sigma_v=0.20, sigma_i=0.10)


def _p(**kw):
    return V0._p(**kw)


def channel_classes(design, defect):
    """Every class the channel carries, with its mass and whether THIS design's check blocks it.

    The check BLOCKS a substitution; it does not make the substitution impossible.  (The first version removed
    the caught classes from the enumeration, which made the attack-success metric blind to exactly what the
    check does -- it could only ever report 1.0 over the survivors.)

    The four classes are a PARTITION of the channel's state space: clean = 1 - (display + subv + subi).  The
    first version wrote clean as (1-delta)(1-sigma_v)(1-sigma_i), a *pipeline* product, so the masses summed to
    1.104: the enumeration measured an expectation over a measure of mass 1.104 while the drawing route used a
    proper partition of the same parameters.  It surfaced as 4 of 6 Monte Carlo cells outside their intervals;
    v0 and v1 both carried a "state space sums to 1" assertion and v2 had dropped it.

    `delta` is not a blocked class but an ABSENT one: a canonical rendering is what makes a re-rendering defect
    impossible, so a design carrying `canonical` does not partition it at all (its mass stays in clean).  The
    drawing route has said so all along (`p_display = 0.0 if spec["canonical"]`); the enumeration must too, or
    the two routes measure two different models -- which the assertion below caught the moment it was added
    (0.7000000000000001 on a canonical design, i.e. delta counted as a class that the design had already removed).
    """
    spec = DESIGN_SPEC[design]
    d = dict(DEFECT)
    d.update(defect or {})
    p_display = 0.0 if spec["canonical"] else d["delta"]
    total = p_display + d["sigma_v"] + d["sigma_i"]
    if total > 1.0 + 1e-12:
        raise RuntimeError("the defect parameters exceed 1: delta + sigma_v + sigma_i = %.17g" % total)
    out = [("clean", 1.0 - total, False)]
    if p_display > 0:
        out.append(("display", p_display, False))
    if d["sigma_v"] > 0:
        out.append(("subv", d["sigma_v"], spec["check"] in ("R", "request")))
    if d["sigma_i"] > 0:
        out.append(("subi", d["sigma_i"], spec["check"] == "request"))
    return out



def surviving_classes(design, defect):
    """Back-compatible view: only the classes this design cannot block."""
    return [(n, m) for n, m, caught in channel_classes(design, defect) if not caught]


def enum_design(params, s, design, defect=None):
    """Exact expectation for one design by summing the channel's state space.

    States: (P, escalated, defect class, human decision).  The defect class decides three things at once -- what
    the human reads, what executes, and whether a block binds -- which is the whole point of the construct.
    """
    spec = DESIGN_SPEC[design]
    pi, a, f = params["pi"], params["a"], params["f"]
    L, c, cb = params["L"], params["c"], params["cb"]
    if not spec["gate"]:
        return L * pi, dict(harm=pi, attention=0.0, false_block=0.0, attack_success=None)
    harm = att = fb = 0.0
    subst_attempts = subst_run = 0.0
    classes = channel_classes(design, defect)
    _tot = sum(m for _n, m, _c in classes)
    if abs(_tot - 1.0) > 1e-12:
        raise RuntimeError("the channel's class masses do not sum to 1: %.17g" % _tot)
    for name, mass, caught in classes:
        if mass <= 0.0:
            continue
        for P_harm in (True, False):
            for esc in (True, False):
                if name == "clean":
                    render_harm, exec_harm, binds = P_harm, P_harm, True
                elif name == "display":
                    render_harm, exec_harm, binds = False, P_harm, True
                else:
                    render_harm, exec_harm, binds = P_harm, True, False
                p_reject = (a if render_harm else f) if esc else 0.0
                for reject in (True, False):
                    prob = (mass * (pi if P_harm else 1.0 - pi) * (s if esc else 1.0 - s)
                            * (p_reject if reject else 1.0 - p_reject))
                    blocked = (esc and reject and binds) or caught
                    executes = not blocked
                    if exec_harm and executes:
                        harm += prob
                    if esc:
                        att += prob
                    if (not P_harm) and blocked and not caught:
                        # the same rule the drawing route applies: a harmless execution forgone.  The
                        # reviewer's own false positive in a substitution class is NOT one either -- the
                        # rejection does not bind there (binds is False), so it changed nothing.
                        fb += prob
                    if name in ("subv", "subi"):
                        subst_attempts += prob
                        if executes:
                            subst_run += prob
    return (L * harm + c * att + cb * fb,
            dict(harm=harm, attention=att, false_block=fb,
                 attack_success=(subst_run / subst_attempts) if subst_attempts > 0 else None))



def simulate_design_per(params, s, design, defect=None, n=400000, seed=20260921):
    """The draw, ALSO returning its PER-ACTION loss array, so a caller can resample the sample it read.

    `simulate_design` is this function with the array reduced away -- there is ONE class model, not two.  A
    caller that wants a bootstrap needs the individual draws, not their mean: the mean is the thing being
    resampled.  (The no-gate design returns `per = None`: its value is exact, so its sample carries no
    uncertainty to resample, and a caller must treat that as a third state rather than as a zero-variance draw.)
    """
    spec = DESIGN_SPEC[design]
    d = dict(DEFECT)
    d.update(defect or {})
    pi, a, f = params["pi"], params["a"], params["f"]
    L, c, cb = params["L"], params["c"], params["cb"]
    rng = np.random.default_rng(seed)
    if not spec["gate"]:
        return L * pi, None, None
    P = rng.random(n) < pi
    E = rng.random(n) < s
    u = rng.random(n)
    # every class is DRAWN; the check blocks rather than prevents.  (The first version removed the caught
    # classes here, which made the drawn attack-success disagree with the exact value -- 1.0 against 0.3333 --
    # because a rate over survivors cannot see what the check did.)
    p_display = 0.0 if spec["canonical"] else d["delta"]
    p_subv = d["sigma_v"]
    p_subi = d["sigma_i"]
    edges = np.cumsum([p_display, p_subv, p_subi])
    rest = rng.random(n)
    cls = np.full(n, "clean", dtype="U6")
    cls = np.where(rest < edges[0], "display", cls)
    cls = np.where((rest >= edges[0]) & (rest < edges[1]), "subv", cls)
    cls = np.where((rest >= edges[1]) & (rest < edges[2]), "subi", cls)
    render_harm = np.where(cls == "display", False, P)
    exec_harm = np.where(np.isin(cls, ["subv", "subi"]), True, P)
    binds = ~np.isin(cls, ["subv", "subi"])
    reject = u < (np.where(render_harm, a, f) * E)
    caught = ((cls == "subv") & (spec["check"] in ("R", "request"))) | ((cls == "subi") & (spec["check"] == "request"))
    blocked = (E & reject & binds) | caught
    executes = ~blocked
    # false block = a HARMLESS EXECUTION FORGONE: the state would have executed harmlessly without the
    # gate, and the gate stopped it.  `(~P) & blocked` alone is not that -- it also counts a caught
    # substitution of a legitimate request, where no gate the state would have executed the SUBSTITUTE
    # (harmfully), so the block destroyed nothing.  The enumeration has always excluded it (`and not
    # caught`); the first version of this route did not, and the two routes then measured two different
    # models: the disagreement was cb * (1-pi) * sigma_caught, 0.0120 at the defaults against an observed
    # 0.0121 (D4) and 0.0080 against 0.0076/0.0074 (D3/D5) -- 25 standard errors.  Charging it would also
    # be asymmetric: the no-gate baseline E0 = L*pi carries no service term, so the gate would be billed
    # for a lost harmless execution that the channel, not the gate, took away.
    fb_mask = (~P) & blocked & (~caught)
    loss = (float(np.sum(L * (exec_harm & executes))) + c * float(np.sum(E))
            + cb * float(np.sum(fb_mask))) / n
    per = (L * (exec_harm & executes).astype(float) + c * E.astype(float)
           + cb * fb_mask.astype(float))
    sub = np.isin(cls, ["subv", "subi"])
    attack = float(np.sum(sub & executes)) / float(np.sum(sub)) if sub.any() else None
    return loss, per, attack


def simulate_design(params, s, design, defect=None, n=400000, seed=20260921):
    """The same quantity by drawing -- a second route to every number above.

    The array `simulate_design_per` returns is reduced here to the interval this route has always reported; the
    draw itself is not duplicated, so the two entries cannot drift apart.
    """
    loss, per, attack = simulate_design_per(params, s, design, defect=defect, n=n, seed=seed)
    if per is None:                       # the no-gate design: its value is exact, so its interval is a point
        return loss, (loss, loss), attack
    se = float(per.std(ddof=1) / math.sqrt(n))
    return loss, (loss - 1.96 * se, loss + 1.96 * se), attack


def value(params, s, design, defect=None):
    """V = E0 - E1, the design's per-action value against the no-gate baseline."""
    loss, _ = enum_design(params, s, design, defect)
    return params["L"] * params["pi"] - loss


def main():
    res = {"what": "issue #93 v2 -- the design axis: is the use-time check an independent repair? (PB4)",
           "why": "PB4 registers the repair as fidelity-equivalent, not independent; the published claim is the "
                  "opposite",
           "preregistered": dict(
               P1="no defects -> every gated design equals v1's b=1 screening value; D0 equals L*pi",
               P2="V(D3) > V(D2) strictly iff sigma_v > 0",
               P3="V(D4) - V(D3) > 0 strictly iff sigma_i > 0, monotone, zero at sigma_i = 0",
               P4="V(D3) - V(D5) > 0 strictly iff delta > 0 (the check cannot read the display class)",
               P5="D0 worst; D1 <= D2 <= D3 <= D4; the published ordering holds",
               P6="channel closed -> attack success exactly 0; channel open -> higher at every design"),
           "designs": DESIGN_SPEC, "defect_defaults": DEFECT}
    report = []

    def say(line=""):
        print(line)
        report.append(line)

    base = _p()
    S = 1.0

    # ---- P1 controls
    say("=== P1  controls: no defects, and the baseline")
    clean = dict(delta=0.0, sigma_v=0.0, sigma_i=0.0)
    v1scr = V1.value_closed(base, "none", 1.0, S)
    rows, worst = [], 0.0
    for design in DESIGNS[1:]:
        v = value(base, S, design, clean)
        d = abs(v - v1scr)
        worst = max(worst, d)
        rows.append(dict(design=design, value=v, v1_screening=v1scr, abs_diff=d))
    # The no-gate design's LOSS is L*pi; its VALUE is 0 by definition (E1 = E0).  The first version of this
    # control asserted value == L*pi and was reading the wrong object -- the same "a property measured at the
    # wrong point" shape this round's sibling (Class 100) records for b = 0 vs s = 0.
    d0_loss, _dec0 = enum_design(base, S, "D0")
    d0 = value(base, S, "D0")
    res["P1_controls"] = dict(rows=rows, worst_abs_diff=worst, d0_loss=d0_loss, d0_value=d0,
                              baseline=base["L"] * base["pi"])
    say("  no defects: every gated design equals v1's b=1 screening value %.6f (worst diff %.3e)"
        % (v1scr, worst))
    say("  D0: loss = %.6f vs L*pi = %.6f (%s); value = %.6f (0 by definition, E1 = E0)"
        % (d0_loss, base["L"] * base["pi"],
           "equal" if abs(d0_loss - base["L"] * base["pi"]) < 1e-15 else "DIFFERENT", d0))
    if worst > 1e-12:
        raise RuntimeError("a gated design does not reduce to v1's screening case: %.3e" % worst)
    if abs(d0_loss - base["L"] * base["pi"]) > 1e-15:
        raise RuntimeError("the no-gate design's loss is not L*pi: %.17g" % d0_loss)
    if abs(d0 - 0.0) > 1e-15:
        raise RuntimeError("the no-gate design's value is not 0: %.17g" % d0)
    say("  -> the design axis extends the same model: with a perfect channel every gate is the v1 screening case")

    # ---- the design ladder at the defaults
    say()
    say("=== the design ladder at the defaults (delta=%.2f sigma_v=%.2f sigma_i=%.2f s=%.1f)"
        % (DEFECT["delta"], DEFECT["sigma_v"], DEFECT["sigma_i"], S))
    table = []
    for design in DESIGNS:
        v = value(base, S, design)
        _l, dec = enum_design(base, S, design)
        table.append(dict(design=design, value=v, harm=dec["harm"], attention=dec["attention"],
                          false_block=dec["false_block"], attack_success=dec["attack_success"]))
        say("  %-3s value %+.6f   harm %.6f  attention %.6f  false-block %.6f  attack-success %s"
            % (design, v, dec["harm"], dec["attention"], dec["false_block"],
               "n/a" if dec["attack_success"] is None else "%.4f" % dec["attack_success"]))
    res["design_table"] = table
    V = {r["design"]: r["value"] for r in table}

    # ---- P5 ordering.  The registration's external-validation arm is stated in ATTACK-SUCCESS terms ("the
    # unbound arm must be worst in the reported 68-100% band"), so it is read there; the VALUE ordering is a
    # separate read, and it carries this round's first substantive finding: an unbound gate over a defective
    # channel can be worth LESS than no gate at all (PB1's registered failure region).
    atk = {r["design"]: r["attack_success"] for r in table}
    unbound = ("D1", "D2")
    p5 = dict(unbound_is_worst=bool(all(atk[d] is not None and atk[d] >= 0.999 for d in unbound)),
              checked_reduces=bool(atk["D3"] is not None and atk["D3"] < min(atk[d] for d in unbound)),
              rederived_reaches_zero=bool(atk["D4"] is not None and abs(atk["D4"]) < 1e-15),
              vac_beats_unbound=bool(V["D3"] > V["D1"]),
              value_monotone_D1_to_D4=bool(all([V[d] for d in ("D1", "D2", "D3", "D4")][k]
                                               <= [V[d] for d in ("D1", "D2", "D3", "D4")][k + 1] + 1e-15
                                               for k in range(3))),
              gate_worse_than_no_gate=[d for d in DESIGNS[1:] if V[d] < V["D0"] - 1e-15],
              attack_success=atk, values=V)
    res["P5_ordering"] = p5
    say("  attack success: unbound %s (band >= 0.999) | check reduces it %s | re-derived reaches 0 %s"
        % (p5["unbound_is_worst"], p5["checked_reduces"], p5["rederived_reaches_zero"]))
    say("  value ordering D1<=D2<=D3<=D4 %s ; designs worth LESS than no gate: %s"
        % (p5["value_monotone_D1_to_D4"], p5["gate_worse_than_no_gate"] or "none"))
    if not (p5["unbound_is_worst"] and p5["checked_reduces"] and p5["rederived_reaches_zero"]
            and p5["vac_beats_unbound"] and p5["value_monotone_D1_to_D4"]):
        raise RuntimeError("the design ordering misses the external-validation arm: %s" % p5)

    # ---- P2
    say()
    say("=== P2  the check has real value exactly where the channel is R-VISIBLE")
    p2 = []
    for sv in (0.0, 0.1, 0.2, 0.4):
        dd = dict(DEFECT, sigma_v=sv)
        gain = value(base, S, "D3", dd) - value(base, S, "D2", dd)
        p2.append(dict(sigma_v=sv, gain=gain))
        say("  sigma_v=%.2f  V(D3) - V(D2) = %+.6f" % (sv, gain))
    res["P2_check_value"] = dict(rows=p2, zero_when_absent=bool(abs(p2[0]["gain"]) < 1e-15),
                                 positive_when_present=bool(all(r["gain"] > 1e-12 for r in p2[1:])))
    if not (res["P2_check_value"]["zero_when_absent"] and res["P2_check_value"]["positive_when_present"]):
        raise RuntimeError("the check's value does not follow sigma_v: %s" % p2)

    # ---- P3
    say()
    say("=== P3  the check's BLIND SPOT is exactly sigma_i (re-derived vs reading the same R)")
    p3 = []
    for si in (0.0, 0.05, 0.1, 0.3):
        dd = dict(DEFECT, sigma_i=si)
        gap = value(base, S, "D4", dd) - value(base, S, "D3", dd)
        p3.append(dict(sigma_i=si, gap=gap))
        say("  sigma_i=%.2f  V(D4) - V(D3) = %+.6f" % (si, gap))
    res["P3_blind_spot"] = dict(rows=p3, zero_when_absent=bool(abs(p3[0]["gap"]) < 1e-15),
                                positive_when_present=bool(all(r["gap"] > 1e-12 for r in p3[1:])),
                                monotone=bool(all(p3[k]["gap"] <= p3[k + 1]["gap"] + 1e-15
                                                  for k in range(len(p3) - 1))))
    if not (res["P3_blind_spot"]["zero_when_absent"] and res["P3_blind_spot"]["positive_when_present"]
            and res["P3_blind_spot"]["monotone"]):
        raise RuntimeError("the same-representation check's blind spot does not follow sigma_i: %s" % p3)

    # ---- P4
    say()
    say("=== P4  the check does NOT repair the DISPLAY class (the falsifier of 'independent')")
    p4 = []
    for dl in (0.0, 0.15, 0.3, 0.5):
        dd = dict(DEFECT, delta=dl)
        gap = value(base, S, "D3", dd) - value(base, S, "D5", dd)
        p4.append(dict(delta=dl, gap=gap))
        say("  delta=%.2f  V(D3) - V(D5) = %+.6f  (the canonical rendering's own value, which a check reading R"
            % (dl, gap))
        say("            cannot supply: a display defect is invisible in R)")
    res["P4_display_blind"] = dict(rows=p4, zero_when_absent=bool(abs(p4[0]["gap"]) < 1e-15),
                                   positive_when_present=bool(all(r["gap"] > 1e-12 for r in p4[1:])))
    if not (res["P4_display_blind"]["zero_when_absent"] and res["P4_display_blind"]["positive_when_present"]):
        raise RuntimeError("the check appears to repair the display class: %s" % p4)

    # ---- the residual channel
    say()
    say("=== the residual channel: which defect survives which design")
    residual = {}
    for design in DESIGNS[1:]:
        residual[design] = [name for name, _m in surviving_classes(design, DEFECT) if name != "clean"]
    res["residual_channel"] = residual
    for design in DESIGNS[1:]:
        say("  %-3s survives: %s" % (design, ", ".join(residual[design]) or "nothing"))

    # ---- P6: the published anchor, read where the anchor's own claim lives
    say()
    say("=== P6  the published anchor (2609.18411: 68-100% attack success unbound, 0% with binding)")
    p6 = []
    for dd, label in ((dict(DEFECT, sigma_v=0.3, sigma_i=0.0), "channel fully R-visible"),
                      (dict(DEFECT, sigma_v=0.3, sigma_i=0.1), "10% of it R-invisible"),
                      (dict(DEFECT, sigma_v=0.3, sigma_i=0.3), "half of it R-invisible")):
        row = dict(label=label)
        for d in ("D1", "D3", "D4"):
            row[d] = enum_design(base, S, d, dd)[1]["attack_success"]
        exp = dd["sigma_i"] / (dd["sigma_v"] + dd["sigma_i"])
        row["predicted_D3"] = exp
        row["D3_matches_sigma_share"] = bool(abs(row["D3"] - exp) < 1e-12)
        p6.append(row)
        say("  %-22s D1 %.4f   D3 %.4f (predicted sigma_i/(sigma_v+sigma_i) = %.4f)   D4 %.4f"
            % (label, row["D1"], row["D3"], exp, row["D4"]))
    res["P6_anchor"] = p6
    say("  -> the published \"0% with binding\" is reproduced EXACTLY where the channel is fully R-visible")
    say("     (%.4f), and nowhere else: at 10%% R-invisible the same design leaves %.4f of the attacks running."
        % (p6[0]["D3"], p6[1]["D3"]))
    if not all(r["D3_matches_sigma_share"] for r in p6):
        raise RuntimeError("D3's attack success is not the R-invisible share: %s" % p6)
    if not (abs(p6[0]["D3"]) < 1e-15 and p6[1]["D3"] > 0 and p6[2]["D3"] > p6[1]["D3"]):
        raise RuntimeError("the anchor's zero-attack case is not isolated: %s" % p6)
    if not all(abs(r["D4"]) < 1e-15 for r in p6):
        raise RuntimeError("the re-derived check does not close the channel: %s" % p6)

    # ---- the Monte Carlo route
    say()
    say("=== the Monte Carlo route (a second route to the design values)")
    mc, covered, biases = [], 0, []
    for design in DESIGNS:
        exact = value(base, S, design)
        draw, CI, attack = simulate_design(base, S, design, n=400000, seed=9100 + len(design))
        mc_v = base["L"] * base["pi"] - draw
        # The interval is read against the EXACT design loss, not against the draw it was centred on: a
        # centre is always inside its own interval, so the first version of this control could never fail
        # (the mutation battery caught that -- no mutation could make it fire).
        exact_loss, _dec = enum_design(base, S, design)
        inside = bool(CI[0] <= exact_loss <= CI[1])
        covered += int(inside)
        biases.append(draw - (base["L"] * base["pi"] - exact))
        mc.append(dict(design=design, exact=exact, mc=mc_v, in_ci=inside, attack_success=attack))
        say("  %-3s exact %+.6f  drawn %+.6f  attack %s  %s"
            % (design, exact, mc_v, "n/a" if attack is None else "%.4f" % attack,
               "inside" if inside else "OUT"))
    bias = float(np.mean(biases))
    bias_se = float(np.std(biases, ddof=1) / np.sqrt(len(biases)))
    res["monte_carlo"] = dict(rows=mc, covered=covered, n=len(mc), bias=bias, bias_se=bias_se,
                              bias_in_band=bool(abs(bias) <= 3 * bias_se))
    say("  covered %d of %d; mean bias %+.3e +- %.3e (%s)"
        % (covered, len(mc), bias, bias_se, "consistent with zero" if abs(bias) <= 3 * bias_se else "BIASED"))
    if covered < len(mc) - 1:
        raise RuntimeError("the Monte Carlo route missed its interval in %d cells" % (len(mc) - covered))
    if abs(bias) > 3 * bias_se:
        raise RuntimeError("the drawn design values are biased: %.3e +- %.3e" % (bias, bias_se))

    # ---- the headline
    say()
    say("=== the headline: the check's marginal value, and what bounds it")
    say("  at delta=%.2f sigma_v=%.2f sigma_i=%.2f, s=1.0:" % (DEFECT["delta"], DEFECT["sigma_v"], DEFECT["sigma_i"]))
    say("    V(D2) canonical rendering only   %+.6f" % V["D2"])
    say("    V(D3) + check reading R          %+.6f   (the check's own value: %+.6f)"
        % (V["D3"], V["D3"] - V["D2"]))
    say("    V(D4) + check re-derived         %+.6f   (what the same-R check cannot reach: %+.6f)"
        % (V["D4"], V["D4"] - V["D3"]))
    say("    V(D5) check without canonical    %+.6f   (the display class it never reads: %+.6f)"
        % (V["D5"], V["D3"] - V["D5"]))
    say("  -> PB4's registered direction is confirmed in its measurable form: the same-representation check")
    say("     recovers only the R-visible part of the channel; its residual is exactly sigma_i, the part of")
    say("     the channel invisible in the representation it reads.  The published claim -- that the check is")
    say("     independent of the rendering -- fails twice: it cannot read sigma_i, and it cannot read delta.")
    res["headline"] = dict(D2=V["D2"], D3=V["D3"], D4=V["D4"], D5=V["D5"],
                           check_own_value=V["D3"] - V["D2"],
                           unreachable_by_same_R=V["D4"] - V["D3"],
                           display_unrepaired=V["D3"] - V["D5"])

    res["build"] = dict(python="%s.%s.%s" % tuple(map(str, sys.version_info[:3])), numpy=np.__version__,
                        script_crc32="%08x" % zlib.crc32(io.open(os.path.abspath(__file__), "rb").read()))
    res["report_sha256"] = "%08x" % zlib.crc32(("\n".join(report)).encode("utf-8"))
    with io.open(OUT, "w") as fh:
        json.dump(res, fh, indent=1, sort_keys=True)
    say()
    say("wrote %s" % OUT)
    say("report id %s  (crc32 of this report; a different build may move it)" % res["report_sha256"])


if __name__ == "__main__":
    main()
