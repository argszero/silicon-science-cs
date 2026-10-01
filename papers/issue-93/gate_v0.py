#!/usr/bin/env python3
"""#93 v0 -- the approval gate's SCREENING case in closed form, and the harness that must agree with it.

WHAT THIS ROUND IS FOR.  The registration's question is where the net value of a human approval gate changes
sign, and its construct is *binding fidelity* `b`: does the object the human reviews denote the object that
executes?  Before any cell of that map is read, the harness that will read it must be shown to compute a case
whose answer is known in closed form -- and the case that is known is the one where the channel is faithful
(`b = 1`, the screening-only case the deployed field assumes).  So this file builds the harness in its FULL
form (four gate designs, three adversary variants, `b` a parameter) and reads ONLY the closure: the screening
case, exactly, three independent ways.

    1. ROUTE A -- closed form.  Algebra for the screening case, written from the model's statement.
    2. ROUTE B -- exact enumeration.  A sum over the discrete state space (proposed type x escalation x
       rendering x decision x execution), each state carrying its own probability and its own loss.  Written
       as a state loop, not as the algebra, so that a missing state or a sign error shows up as a difference.
    3. ROUTE C -- Monte Carlo.  Draws, with declared seeds and an interval.  A different route to the same
       number, and the only one of the three that can be wrong in the way a simulation is wrong.

    A and B must agree to floating point; C must lie inside its own interval, and its measured event
    frequencies must agree with the enumeration's exact probabilities.

THE MODEL (v0).  One action at a time, one human gate.

    proposed action   P ~ Bernoulli(pi), harmful with probability pi; a harmful action that EXECUTES costs L
    escalation        E ~ Bernoulli(s), independent of P and of b; one escalation costs c (human attention)
    fidelity          F ~ Bernoulli(b).  Faithful: the rendering denotes what executes and the decision binds.
                      Unfaithful: the ADVERSARY VARIANT decides what happens, and the three variants are the
                      three mechanisms the field's 2026-09 papers report --
                        'none'         no adversary exists: R = P and the decision binds (the screening case)
                        'mismatch'     representation mismatch: the human is shown a BENIGN rendering of a
                                       harmful action, so the decision is about another object
                        'substitution' post-approval state substitution: the human sees the truth, and the
                                       executed action is replaced by the harmful one -- the same event that
                                       also defeats a rejection (a block that does not bind)
    rendering R       faithful -> R = P.   'mismatch' -> R = benign.   'substitution' -> R = P.
    executed action A faithful -> A = P.   'mismatch' -> A = P.        'substitution' -> A = harmful
    decision D        the human judges R: reject with probability `a` if R is harmful (sensitivity), with
                      probability `f` if R is benign (false positive).  A rejection blocks the action unless a
                      'substitution' draw has made the block non-binding.
    loss              L*[A is harmful and the action executes] + c*[escalated] + cb*[P is benign and blocked].
                      A SUBSTITUTED harmful action costs eta*L instead of L: eta=1 is the natural reading (the
                      substituted action is as harmful as the one the adversary meant to run) and is the value
                      every read in this round takes; eta is a parameter because a substitution need not
                      reproduce the proposed action's severity, and that is a later round's question.

    The screening case is `variant == 'none'`, and equivalently ANY variant at `b = 1` -- which is the control
    that matters: the adversary machinery must be INERT at b = 1 and must FIRE at b = 0, both exactly.

WHAT THIS ROUND DOES **NOT** READ.  The map (b < 1), the four designs' comparison, and the escalation optimum
are later rounds' objects.  The map is guarded: `screen_only=True` refuses any read at b < 1, so the round
cannot read the map by accident -- a control that can fail, not a promise.

Run:  /usr/bin/python3 gate_v0.py          (writes gate_v0_results.json beside itself)
"""
import io
import json
import math
import os
import zlib

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "gate_v0_results.json")

VARIANTS = ("none", "mismatch", "substitution")

# ---------------------------------------------------------------- parameters
DEFAULT = dict(pi=0.20, a=0.80, f=0.05, L=1.0, c=0.02, cb=0.05, eta=1.0)


def _p(**kw):
    d = dict(DEFAULT)
    d.update(kw)
    return d


# ---------------------------------------------------------------- route A: closed form (screening case)
def closed_form(params, s):
    """The screening case's expected loss per action, from the model's algebra.

    E[harm]      = L * pi * [(1-s) + s(1-a)]        a harmful action survives if it is not escalated, or is
                                                    escalated and mis-approved
    E[attention] = c * s                            every escalation costs one review
    E[falseblock]= cb * (1-pi) * s * f              a benign action is blocked when the human sees it and
                                                    rejects it
    """
    pi, a, f = params["pi"], params["a"], params["f"]
    L, c, cb = params["L"], params["c"], params["cb"]
    return L * pi * ((1.0 - s) + s * (1.0 - a)) + c * s + cb * (1.0 - pi) * s * f


def closed_form_value(params, s):
    """The gate's per-action value against the no-gate baseline: E0 - E1."""
    return params["L"] * params["pi"] - closed_form(params, s)


def closed_form_threshold(params):
    """The reviewer accuracy at which the screening case's value changes sign (value = 0 at s > 0)."""
    pi, f = params["pi"], params["f"]
    L, c, cb = params["L"], params["c"], params["cb"]
    return (c + cb * (1.0 - pi) * f) / (L * pi)


# ---------------------------------------------------------------- route B: exact enumeration
def enumerate_exact(params, s, variant="none", b=1.0, screen_only=True):
    """Exact expectation by summing the discrete state space.  Returns (loss, decomposition).

    States: (P, escalated, faithful, decision) -- decision independent of everything but the RENDERING, which
    is a deterministic function of (variant, faithful, P).
    """
    if screen_only and b < 1.0:
        raise RuntimeError("v0 reads the screening case only (b=1); the map is a later round's object")
    pi, a, f = params["pi"], params["a"], params["f"]
    L, c, cb = params["L"], params["c"], params["cb"]
    eta = params["eta"]                    # the harm of a SUBSTITUTED action, as a fraction of L
    loss = harm = attention = false_block = 0.0
    total_p = 0.0
    for P_harm in (True, False):
        p_P = pi if P_harm else (1.0 - pi)
        for esc in (True, False):
            p_E = s if esc else (1.0 - s)
            for faithful in (True, False):
                p_F = b if faithful else (1.0 - b)
                substituted = False
                if faithful or variant == "none":
                    render_harm = P_harm                       # the human reads the true object
                    exec_harm = P_harm
                    binds = True
                elif variant == "mismatch":
                    render_harm = False                        # the human reads a benign rendering
                    exec_harm = P_harm                         # what executes is unchanged
                    binds = True
                else:                                          # substitution
                    render_harm = P_harm                       # the human reads the truth
                    exec_harm = True                           # what executes has been replaced
                    binds = False                              # and the decision does not bind
                    substituted = not P_harm                   # a benign action became the harmful one
                p_reject = (a if render_harm else f) if esc else 0.0
                for reject in (True, False):
                    p_D = p_reject if reject else (1.0 - p_reject)
                    prob = p_P * p_E * p_F * p_D
                    blocked = esc and reject and binds
                    executes = not blocked
                    if exec_harm and executes:
                        loss += prob * (eta * L if substituted else L)
                        harm += prob
                    if esc:
                        loss += prob * c
                        attention += prob
                    if (not P_harm) and blocked:
                        loss += prob * cb
                        false_block += prob
                    total_p += prob
    if abs(total_p - 1.0) > 1e-12:
        raise RuntimeError("the state space does not sum to 1: %.17g" % total_p)
    return loss, dict(harm=harm, attention=attention, false_block=false_block)


# ---------------------------------------------------------------- route C: Monte Carlo
def simulate(params, s, variant="none", b=1.0, n=400000, seed=20260921, screen_only=True):
    """The same quantity by drawing, with an interval.  A different route to the same number."""
    if screen_only and b < 1.0:
        raise RuntimeError("v0 reads the screening case only (b=1); the map is a later round's object")
    pi, a, f = params["pi"], params["a"], params["f"]
    L, c, cb = params["L"], params["c"], params["cb"]
    eta = params["eta"]
    rng = np.random.default_rng(seed)
    P = rng.random(n) < pi
    E = rng.random(n) < s
    F = rng.random(n) < b
    substituted = np.zeros(n, dtype=bool)
    if variant == "none":
        render_harm, exec_harm, binds = P.copy(), P.copy(), np.ones(n, dtype=bool)
    elif variant == "mismatch":
        render_harm = np.where(F, P, False)
        exec_harm, binds = P.copy(), np.ones(n, dtype=bool)
    else:
        render_harm = P.copy()
        exec_harm = np.where(F, P, True)
        binds = F.copy()
        substituted = (~F) & (~P)          # a benign action replaced by the harmful one
    u = rng.random(n)
    p_reject = np.where(render_harm, a, f) * E
    reject = u < p_reject
    blocked = E & reject & binds
    executes = ~blocked
    severity = np.where(substituted, eta * L, L)
    harm_count = float(np.sum(exec_harm & executes))
    att_count = float(np.sum(E))
    fb_count = float(np.sum((~P) & blocked))
    loss = (float(np.sum(severity * (exec_harm & executes))) + c * att_count + cb * fb_count) / n
    # interval on the mean of the per-action loss
    per = (severity * (exec_harm & executes).astype(float) + c * E.astype(float) + cb * ((~P) & blocked).astype(float))
    # The number this route REPORTS and the number its interval is built from are two expressions of one
    # quantity -- one from event counts, one from the per-action array.  Nothing tied them together, and a
    # mutated copy that biased one alone still ran to completion: the reading is a claim with no owner until
    # this line exists.  The tolerance is calibrated, not guessed: over this round's 62 simulate calls the worst
    # disagreement is 8.9e-16, so 1e-12 sits ~1100x above float noise and four orders below any real defect.
    if abs(float(per.mean()) - loss) > 1e-12:
        raise RuntimeError("the reported estimate and the interval's centre are one quantity written twice and "
                           "they disagree: %.17g vs %.17g" % (loss, float(per.mean())))
    se = float(per.std(ddof=1) / math.sqrt(n))
    return loss, (loss - 1.96 * se, loss + 1.96 * se), se, dict(
        harm=harm_count / n, attention=att_count / n, false_block=fb_count / n)


# ---------------------------------------------------------------- the round's readings
def main():
    res = {"what": "issue #93 v0 -- the screening case's closure check, and the harness's controls",
           "scope": "screening case only (b = 1, or variant 'none'); the map (b < 1) is guarded, not read"}
    report = []

    def say(line=""):
        print(line)
        report.append(line)

    # ---- 1. the closure: three routes over a parameter grid
    say("=== 1. closure of the screening case (routes A, B, C must agree)")
    grid = [_p(), _p(pi=0.05), _p(pi=0.5, a=0.6), _p(a=0.3, f=0.2), _p(a=0.95, f=0.0),
            _p(L=5.0, c=0.1, cb=0.2), _p(pi=0.02, a=0.99, f=0.5)]
    s_grid = [0.0, 0.25, 0.5, 1.0]
    closure, worst = [], 0.0
    for pi_ in grid:
        for s in s_grid:
            A = closed_form(pi_, s)
            B, decB = enumerate_exact(pi_, s)
            C, CI, se, decC = simulate(pi_, s, n=400000, seed=20260921 + int(1000 * s) + int(100 * pi_["pi"]))
            d = abs(A - B)
            worst = max(worst, d)
            closure.append(dict(pi=pi_["pi"], a=pi_["a"], f=pi_["f"], L=pi_["L"], c=pi_["c"], cb=pi_["cb"],
                                s=s, closed_form=A, enumerated=B, mc=C, mc_ci=list(CI),
                                abs_diff_AB=d, in_ci=bool(CI[0] <= B <= CI[1]),
                                dec_exact=decB, dec_mc=decC))
        say("  pi=%.2f a=%.2f f=%.3f L=%.1f c=%.3f cb=%.3f  " % (pi_["pi"], pi_["a"], pi_["f"], pi_["L"],
                                                               pi_["c"], pi_["cb"])
            + " | ".join("s=%.2f A=%.6f B=%.6f C=%.6f%s" % (r["s"], r["closed_form"], r["enumerated"],
                                                            r["mc"], "" if r["in_ci"] else " OUT")
                         for r in closure[-4:]))
    res["closure"] = closure
    res["closure_worst_abs_diff_AB"] = worst
    say("  worst |A - B| over the %d cells: %.3e" % (len(closure), worst))
    covered = sum(r["in_ci"] for r in closure)
    misses = len(closure) - covered
    # A 95 % interval is a 95 % statement: over N cells the expected number of misses is 0.05*N, so requiring
    # every cell to cover is a mis-specified control (it would fail with probability 1 as N grows).  What is
    # read here is the COUNT against its binomial band, and the estimator's BIAS -- the mean signed deviation
    # against the standard error of that mean, which no single interval can see.
    bias = sum(r["mc"] - r["enumerated"] for r in closure) / len(closure)
    bias_se = math.sqrt(sum((r["mc_ci"][1] - r["mc_ci"][0]) ** 2 / (2 * 1.96) ** 2 for r in closure)) / len(closure)
    res["closure_coverage"] = dict(cells=len(closure), covered=covered, misses=misses,
                                   expected_misses=0.05 * len(closure), bias=bias, bias_se=bias_se,
                                   bias_in_band=bool(abs(bias) <= 3 * bias_se))
    say("  Monte Carlo inside its 95%% interval in %d of %d cells (%d misses; %.1f expected at 5%%)"
        % (covered, len(closure), misses, 0.05 * len(closure)))
    say("  the estimator's bias: mean(drawn - exact) = %+.3e +- %.3e (%.2f se) -> %s"
        % (bias, bias_se, abs(bias) / bias_se, "consistent with zero" if abs(bias) <= 3 * bias_se
           else "BIASED"))
    if worst > 1e-12:
        raise RuntimeError("routes A and B disagree beyond floating point: %.3e" % worst)
    if misses > 6:                     # P(misses >= 7 | 28 cells, 5%) ~ 4e-4: an alarm, not a judgement
        raise RuntimeError("the Monte Carlo route missed its interval in %d of %d cells" % (misses,
                                                                                            len(closure)))
    if abs(bias) > 3 * bias_se:
        raise RuntimeError("the Monte Carlo estimator is biased: %.3e +- %.3e" % (bias, bias_se))

    # ---- 2. the decomposition: does the Monte Carlo measure the events the enumeration counts?
    say()
    say("=== 2. the event frequencies (the decomposition, exact vs drawn)")
    freq, worst_f = [], 0.0
    for pi_ in grid[:4]:
        for s in (0.25, 1.0):
            _, decB = enumerate_exact(pi_, s)
            _, _, _, decC = simulate(pi_, s, n=400000, seed=777 + int(100 * s))
            row = dict(pi=pi_["pi"], a=pi_["a"], s=s,
                       exact=decB, mc=decC,
                       max_abs_diff=max(abs(decB[k] - decC[k]) for k in decB))
            worst_f = max(worst_f, row["max_abs_diff"])
            freq.append(row)
        say("  pi=%.2f a=%.2f: harm %.6f/%.6f  attention %.6f/%.6f  false-block %.6f/%.6f (exact/drawn)"
            % (pi_["pi"], pi_["a"], freq[-2]["exact"]["harm"], freq[-2]["mc"]["harm"],
               freq[-2]["exact"]["attention"], freq[-2]["mc"]["attention"],
               freq[-2]["exact"]["false_block"], freq[-2]["mc"]["false_block"]))
    res["frequencies"] = freq
    res["frequencies_worst_abs_diff"] = worst_f
    say("  worst |exact - drawn| over the %d reads: %.3e (Monte Carlo error, not a defect)" % (len(freq),
                                                                                              worst_f))
    if worst_f > 0.01:
        raise RuntimeError("the drawn frequencies are outside Monte Carlo error of the enumeration")

    # ---- 3. the control battery
    say()
    say("=== 3. controls, each of which can fail")
    ctl = {}

    # C1 -- s = 0 is the no-gate baseline, exactly
    p0 = _p()
    B0, _ = enumerate_exact(p0, 0.0)
    C0, CI0, _, _ = simulate(p0, 0.0, n=400000, seed=11)
    ctl["C1_s0_is_the_no_gate_baseline"] = dict(expected=p0["pi"] * p0["L"], enumerated=B0, mc=C0,
                                                mc_ci=list(CI0),
                                                exact=abs(B0 - p0["pi"] * p0["L"]) < 1e-15,
                                                in_ci=CI0[0] <= p0["pi"] * p0["L"] <= CI0[1])
    say("  C1  s=0 -> the no-gate baseline: exact %.17g vs pi*L %.17g (%s); drawn %s"
        % (B0, p0["pi"] * p0["L"], "equal" if ctl["C1_s0_is_the_no_gate_baseline"]["exact"] else "DIFFERENT",
           "inside its interval" if ctl["C1_s0_is_the_no_gate_baseline"]["in_ci"] else "OUTSIDE"))
    if not ctl["C1_s0_is_the_no_gate_baseline"]["exact"]:
        raise RuntimeError("s=0 is not the no-gate baseline: %.17g vs %.17g" % (B0, p0["pi"] * p0["L"]))
    if not ctl["C1_s0_is_the_no_gate_baseline"]["in_ci"]:
        raise RuntimeError("the no-gate baseline left the drawn interval")

    # C2 -- a useless reviewer at full coverage: the gate adds cost and blocks nothing
    p1 = _p(a=0.0, f=0.0)
    B1, _ = enumerate_exact(p1, 1.0)
    want = p1["pi"] * p1["L"] + p1["c"]
    ctl["C2_a0_s1_is_piL_plus_c"] = dict(expected=want, enumerated=B1, abs_diff=abs(B1 - want),
                                         equal=abs(B1 - want) < 1e-15)
    say("  C2  a=0,f=0,s=1 -> pi*L + c: exact %.17g vs %.17g (%s)"
        % (B1, want, "equal" if ctl["C2_a0_s1_is_piL_plus_c"]["equal"] else "DIFFERENT"))
    if not ctl["C2_a0_s1_is_piL_plus_c"]["equal"]:
        raise RuntimeError("a=0,f=0,s=1 is not pi*L + c: %.17g vs %.17g" % (B1, want))

    # C3 -- determinism: two draws at the same seed are the same number
    C3a, _, _, _ = simulate(_p(), 0.5, n=50000, seed=99)
    C3b, _, _, _ = simulate(_p(), 0.5, n=50000, seed=99)
    ctl["C3_determinism"] = dict(a=C3a, b=C3b, bitwise=bool(C3a == C3b))
    say("  C3  same seed, two runs: %s" % ("bitwise identical" if C3a == C3b else "DIFFERENT"))
    if C3a != C3b:
        raise RuntimeError("two draws at the same seed differ: %.17g vs %.17g" % (C3a, C3b))

    # C4 -- the two-sided control on the adversary machinery: inert at b=1, firing at b=0
    p2 = _p(a=1.0, f=0.0)
    inert, fired = {}, {}
    for v in VARIANTS:
        Bv, _ = enumerate_exact(p2, 1.0, variant=v, b=1.0)
        inert[v] = Bv
        Bv0, _ = enumerate_exact(p2, 1.0, variant=v, b=0.0, screen_only=False)
        fired[v] = Bv0
    spread = max(inert.values()) - min(inert.values())
    ctl["C4_inert_at_b1"] = dict(values=inert, spread=spread, inert=spread == 0.0)
    ctl["C4b_fires_at_b0"] = dict(values=fired,
                                  screening=closed_form(p2, 1.0),
                                  mismatch_minus_screening=fired["mismatch"] - closed_form(p2, 1.0),
                                  substitution_minus_screening=fired["substitution"] - closed_form(p2, 1.0),
                                  predicted_mismatch_gap=p2["pi"] * p2["L"] * p2["a"] * 1.0)
    say("  C4a b=1, all three variants: %s (spread %.1e)" % (
        ", ".join("%s=%.17g" % (v, inert[v]) for v in VARIANTS), spread))
    say("      -> %s" % ("the adversary machinery is INERT at b=1, as it must be" if spread == 0.0
                         else "NOT INERT -- the variants differ where no mismatch can occur"))
    say("  C4b b=0, a=1, f=0, s=1: screening %.6f | mismatch %.6f (+%.6f) | substitution %.6f (+%.6f)"
        % (closed_form(p2, 1.0), fired["mismatch"], fired["mismatch"] - closed_form(p2, 1.0),
           fired["substitution"], fired["substitution"] - closed_form(p2, 1.0)))
    say("      -> the predicted mismatch gap is pi*L*a = %.6f, the measured gap is %.6f (%s)"
        % (ctl["C4b_fires_at_b0"]["predicted_mismatch_gap"],
           ctl["C4b_fires_at_b0"]["mismatch_minus_screening"],
           "equal" if abs(ctl["C4b_fires_at_b0"]["mismatch_minus_screening"]
                          - ctl["C4b_fires_at_b0"]["predicted_mismatch_gap"]) < 1e-12 else "DIFFERENT"))
    if spread != 0.0:
        raise RuntimeError("the adversary machinery is not inert at b=1")
    if abs(ctl["C4b_fires_at_b0"]["mismatch_minus_screening"]
           - ctl["C4b_fires_at_b0"]["predicted_mismatch_gap"]) > 1e-12:
        raise RuntimeError("the mismatch arm does not fire with the predicted gap")

    # C4c -- the severity parameter must MOVE the arm it belongs to, and both routes must move together.  The
    # control C4b reads the substitution arm at eta=1 only; a parameter read at one value is not a parameter,
    # it is a constant.  Predicted gap at b=0, s=1, a=1, f=0: L*(pi + (1-pi)*eta) -- pi from the proposed
    # harmful action surviving (nothing binds), (1-pi)*eta from the substituted benign action.
    eta_rows, worst_eta = [], 0.0
    for eta in (0.0, 0.5, 1.0):
        pe = _p(a=1.0, f=0.0, eta=eta)
        Be, _ = enumerate_exact(pe, 1.0, variant="substitution", b=0.0, screen_only=False)
        Ce, CIe, _, _ = simulate(pe, 1.0, variant="substitution", b=0.0, screen_only=False,
                                 n=400000, seed=4242)
        want_e = pe["L"] * (pe["pi"] + (1.0 - pe["pi"]) * eta) + pe["c"]
        worst_eta = max(worst_eta, abs(Be - want_e))
        eta_rows.append(dict(eta=eta, enumerated=Be, predicted=want_e, mc=Ce, mc_ci=list(CIe),
                             in_ci=bool(CIe[0] <= Be <= CIe[1])))
    ctl["C4c_eta_moves_the_substitution_arm"] = dict(rows=eta_rows, worst_abs_diff=worst_eta,
                                                    in_ci=sum(r["in_ci"] for r in eta_rows), of=len(eta_rows))
    say("  C4c substitution arm at b=0, s=1, a=1: " + " | ".join(
        "eta=%.1f exact %.6f predicted %.6f drawn %.6f%s" % (r["eta"], r["enumerated"], r["predicted"],
                                                             r["mc"], "" if r["in_ci"] else " OUT")
        for r in eta_rows))
    say("      -> worst |exact - predicted| %.3e; the arm moves with eta, and the gap from the screening case"
        % worst_eta)
    say("         is exactly L*(pi + (1-pi)*eta), which is the b=0 endpoint of the map the next round reads.")
    if worst_eta > 1e-12:
        raise RuntimeError("the substitution arm does not follow L*(pi + (1-pi)*eta): %.3e" % worst_eta)
    if sum(r["in_ci"] for r in eta_rows) < len(eta_rows) - 1:
        raise RuntimeError("the drawn substitution arm missed its interval in %d of %d eta cells"
                           % (len(eta_rows) - sum(r["in_ci"] for r in eta_rows), len(eta_rows)))

    # C5 -- the guard: the map is refused in v0, on BOTH routes that can read it (the guard has two carriers,
    # and a guard read on one of them is a guard the other can drop)
    ctl["C5_map_is_guarded"] = {}
    for route, fn in (("enumerate", lambda: enumerate_exact(p2, 1.0, variant="mismatch", b=0.5)),
                      ("simulate", lambda: simulate(p2, 1.0, variant="mismatch", b=0.5, n=1000))):
        try:
            fn()
            ctl["C5_map_is_guarded"][route] = "READ -- the guard did not fire"
        except RuntimeError as exc:
            ctl["C5_map_is_guarded"][route] = "refused: %s" % exc
        say("  C5  a map read at b=0.5 by %-9s: %s" % (route, ctl["C5_map_is_guarded"][route]))
    if any(v.startswith("READ") for v in ctl["C5_map_is_guarded"].values()):
        raise RuntimeError("the b<1 guard did not fire on %s"
                           % ", ".join(k for k, v in ctl["C5_map_is_guarded"].items() if v.startswith("READ")))

    # C6 -- the Monte Carlo's coverage over independent seed streams
    cover, p3 = 0, _p(pi=0.3, a=0.7, f=0.1)
    exact3, _ = enumerate_exact(p3, 0.5)
    for k in range(20):
        _, CI, _, _ = simulate(p3, 0.5, n=50000, seed=1000 + k)
        cover += int(CI[0] <= exact3 <= CI[1])
    ctl["C6_mc_coverage_over_20_streams"] = dict(exact=exact3, covered=cover, of=20)
    say("  C6  the exact value inside its 95%% interval in %d of 20 independent streams (nominal 19)" % cover)
    if cover < 16:                     # P(misses >= 5 | 20, 5%) ~ 2.6e-3: an alarm, not a judgement
        raise RuntimeError("the Monte Carlo missed its interval in %d of 20 independent streams" % (20 - cover))

    # ---- 4. what the screening case already says (the v0 reading, no map involved)
    say()
    say("=== 4. the screening case's own structure")
    base = _p()
    thr = closed_form_threshold(base)
    curve = []
    for s in (0.0, 0.25, 0.5, 0.75, 1.0):
        _, dec = enumerate_exact(base, s)
        row = dict(s=s, value=closed_form_value(base, s), decomposition=dec)
        curve.append(row)
        say("  s=%.2f  value E0-E1 = %+.6f  (harm event %.6f, attention %.6f, false-block %.6f, cost %.6f)"
            % (s, row["value"], dec["harm"], dec["attention"], dec["false_block"],
               base["c"] * dec["attention"] + base["cb"] * dec["false_block"]))
    res["screening_curve"] = curve
    res["threshold_a_star"] = thr
    # The slope is read from the CURVE's own ends -- the first version divided the s=0 value (identically 0,
    # since s=0 IS the baseline) by the step, and printed 0.000000 for a curve whose slope is 0.138.  An
    # affineness claim is also checked, not asserted: equal first differences.
    diffs = [curve[k + 1]["value"] - curve[k]["value"] for k in range(len(curve) - 1)]
    slope = (curve[-1]["value"] - curve[0]["value"]) / (curve[-1]["s"] - curve[0]["s"])
    affine_gap = max(diffs) - min(diffs)
    res["screening_curve_affine"] = dict(slope=slope, first_differences=diffs, spread=affine_gap,
                                         affine=bool(affine_gap < 1e-12))
    say("  the value is AFFINE in s (slope %+.6f, first-difference spread %.1e), so the screening case's"
        % (slope, affine_gap))
    say("    optimum is a CORNER, not interior: s* = 1 if the slope is positive, s* = 0 if it is negative --")
    say("    PB3's registered *interior* optimum does not exist at b = 1 (it must be a b<1 phenomenon, which")
    say("    is a later round's object).")
    if affine_gap >= 1e-12:
        raise RuntimeError("the screening case's value is not affine in s: spread %.3e" % affine_gap)
    a_grid = []
    for a in (0.0, 0.2, 0.4, 0.6, 0.8, 1.0):
        pa = _p(a=a)
        a_grid.append(dict(a=a, value=closed_form_value(pa, 1.0)))
        say("  a=%.2f  value at s=1: %+.6f" % (a, a_grid[-1]["value"]))
    res["screening_vs_a"] = a_grid
    sign_changes = [(a_grid[k]["a"], a_grid[k + 1]["a"]) for k in range(len(a_grid) - 1)
                    if a_grid[k]["value"] * a_grid[k + 1]["value"] < 0]
    res["threshold_bracket"] = sign_changes
    say("  the value changes sign at a* = %.4f, bracketed by the grid at %s (the registered PB2 question is"
        % (thr, ", ".join("[%.2f, %.2f]" % b for b in sign_changes)))
    say("    where its SLOPE sits, and this is the screening-case baseline every b<1 cell will be read against).")
    if not sign_changes:
        raise RuntimeError("the value never changes sign on the a grid, so a* = %.4f is not bracketed" % thr)
    if not any(lo <= thr <= hi for lo, hi in sign_changes):
        raise RuntimeError("the closed-form a* = %.4f is not inside the grid's sign-change bracket %s"
                           % (thr, sign_changes))

    res["controls"] = ctl
    res["build"] = dict(python="%s.%s.%s" % tuple(map(str, __import__("sys").version_info[:3])),
                        numpy=np.__version__, script_crc32="%08x" % zlib.crc32(
                            io.open(os.path.abspath(__file__), "rb").read()))
    res["report_sha256"] = "%08x" % zlib.crc32(("\n".join(report)).encode("utf-8"))
    with io.open(OUT, "w") as fh:
        json.dump(res, fh, indent=1, sort_keys=True)
    say()
    say("wrote %s" % OUT)
    say("report id %s  (crc32 of this report; a different build may move it)" % res["report_sha256"])


if __name__ == "__main__":
    main()
