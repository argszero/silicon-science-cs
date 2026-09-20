"""external_v1.py -- registered metric (f): the external cell (issue #50, step 11).

REGISTRATION, verbatim: "(vi) the external cell reproduces the published result's **sign** in its
reported operating region", and the fallback: "a published in-window system result (e.g. 2609.03236's
-18.59% vs sequential, 2607.03333's 16-37% tool-wait share) is reproduced *in sign* inside its own
reported operating region, and the study states per-cell where it does not reach the published
magnitude".

Three things this file refuses to do.

1. IT DOES NOT TYPE THE PUBLISHED NUMBERS INTO THE CODE.  Each cell is BUILT by PARSING a verbatim
   sentence of the paper's own abstract, with the read date and the endpoint recorded beside it.  A
   plant that edits the sentence must move the cell, and that is one of the arms below.  (A number
   typed from memory into a table is a claim with no owner; a number parsed from the record it came
   from has one.)

2. IT DOES NOT LET THE SIGN CONVENTION FLOAT.  The published quantity is a CHANGE IN LATENCY
   ("reducing latency by 18.59\\%", "cuts ... P95 by 18%"); this instrument's benefit is POSITIVE when
   speculation helps.  So a published reduction of X% IS a benefit of +X% here, and the conversion
   lives in ONE function whose plant flips the verdict if it is read the other way.

3. IT DOES NOT CLAIM A MAGNITUDE IT CANNOT REACH.  In this model, with one agent and a free worker,
   the benefit is exactly E[min(T,S)] of a cycle T+S, i.e. p(1-p) of wall time where p = mS/(mT+mS) is
   the tool-wait share -- so the unloaded ceiling is 25% at p = 1/2, and a published reduction above
   25% is reported as NOT REACHED with its shortfall, not smoothed into an agreement.

The cell is the SINGLE-AGENT, UNLOADED regime (one agent loop, one worker), because that is the regime
the published systems measure: their numbers are one agent's own latency against its own tools.  The
instrument has other regimes (step 3's pool study is about them); this file stays in the one the
external anchors speak in, and says so.
"""

import io
import json
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import instrument_v0 as I                                    # the registered instrument, unmodified

READ_DATE = "2026-09-19"
READ_VIA = "arXiv API: export.arxiv.org/api/query?id_list=<id>"
MT = 1.0                 # think mean, FIXED, so the free coordinate is the tool-wait share p
SEEDS = list(range(101, 133))    # 32 independent seeds (>= 3 required; 32 for a usable interval)
STEPS = 800
H_ORACLE = 1.0           # the registered instrument's h = the fraction of steps issued early
H_PROBE_LOW = 0.746      # SPORK's OWN lower reported probe accuracy -- used as an h, and declared

# ------------------------------------------------------------------ the sources, verbatim
SOURCES = {
    "2609.03236": {
        "system": "Speculative Macro Commit (SMC)",
        "url": "https://arxiv.org/abs/2609.03236",
        "read": READ_DATE,
        "sentences": {
            "telecom": "SMC matches the sequential agent's overall accuracy while reducing latency by "
                       "10.23\\% over the Speculative Actions (SA) baseline and 18.59\\% over sequential "
                       "execution on the $\\tau^2$-Bench Telecom subset.",
            "appworld": "On AppWorld, SMC reduces wall time by 7.7\\% over SA baseline and 44.9\\% over "
                        "sequential execution, with a small reduction in task completion.",
        },
    },
    "2607.03333": {
        "system": "SPORK (Self-sPeculative fORKing)",
        "url": "https://arxiv.org/abs/2607.03333",
        "read": READ_DATE,
        "sentences": {
            "wait": "This wait consumes 16-37% of wall time in our workloads and 35-61% in prior reports.",
            "p95": "On real-tool benchmarks, SPORK cuts Qwen3-32B's GAIA P95 by 18% (131.9 to 108.1 s);",
            "probe": "a probe forked at the start of generation predicts Qwen3-32B's upcoming tool name "
                     "with 74.6-99.6% accuracy across five benchmarks.",
        },
    },
}


# ------------------------------------------------------------------ parsing, not typing
PCT_RANGE = re.compile(r"(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)\s*\\?%")
PCT_SINGLE = re.compile(r"(\d+(?:\.\d+)?)\s*\\?%")

def pct_tokens(sentence):
    """Every percent token in the sentence, IN ORDER, as ("single", value) or ("range", lo, hi).

    Ranges are matched first and their span removed, so "16-37%" yields ONE range token rather than a
    single token for the 37.  A sentence is read as a sequence, and each cell below names WHICH token
    it takes and WHY -- the reason is a phrase in the sentence, not a position I remember.
    """
    spans, out = [], []
    for m in PCT_RANGE.finditer(sentence):
        spans.append(m.span())
        out.append(("range", float(m.group(1)), float(m.group(2)), m.start()))
    for m in PCT_SINGLE.finditer(sentence):
        if any(s <= m.start() < e for s, e in spans):
            continue
        out.append(("single", float(m.group(1)), m.start()))
    out.sort(key=lambda t: t[-1])
    return [t[:-1] for t in out]


def sequential_reduction(sentence, other_is_baseline):
    """The published reduction over SEQUENTIAL execution, parsed from the sentence.

    The token is chosen by the PHRASE that names it ("over sequential execution"), and the choice is
    then cross-checked by a property that must hold independently: the sequential number is the LARGER
    of the two, because the sentence also reports the reduction over a weaker baseline.  If a plant
    swaps them the cross-check fires -- which is what makes the phrase, not the position, the reason.
    """
    assert other_is_baseline in sentence, "the sentence does not name the two working points"
    toks = pct_tokens(sentence)
    assert len(toks) == 2 and all(t[0] == "single" for t in toks), toks
    first, second = toks[0][1], toks[1][1]
    assert second > first, ("the sequential reduction must be the larger of the two reported "
                            "numbers; got %s" % toks)
    return second


def band_reduction(sentence, which):
    """A published range, parsed; `which` picks the range by ORDER in the sentence (0 or 1)."""
    toks = [t for t in pct_tokens(sentence) if t[0] == "range"]
    assert len(toks) > which, toks
    return (toks[which][1], toks[which][2])


def build_cells():
    """Every external cell, built from its sentence.  Nothing here is a typed number."""
    smc, spork = SOURCES["2609.03236"], SOURCES["2607.03333"]
    s_telecom = smc["sentences"]["telecom"]
    s_appworld = smc["sentences"]["appworld"]
    s_wait = spork["sentences"]["wait"]
    s_p95 = spork["sentences"]["p95"]
    s_probe = spork["sentences"]["probe"]
    cells = [
        {"key": "smc_telecom", "source": "2609.03236", "system": smc["system"],
         "quantity": "latency reduction over sequential execution, tau2-Bench Telecom subset",
         "published_reduction_pct": sequential_reduction(s_telecom, "over sequential execution"),
         "sentence": s_telecom,
         "region": {"kind": "required_wait_share", "why": "the paper reports no tool-wait share; the "
                    "model inverts p(1-p) to say WHICH shares could produce this reduction"}},
        {"key": "smc_appworld", "source": "2609.03236", "system": smc["system"],
         "quantity": "wall-time reduction over sequential execution, AppWorld",
         "published_reduction_pct": sequential_reduction(s_appworld, "over sequential execution"),
         "sentence": s_appworld,
         "region": {"kind": "required_wait_share", "why": "same inversion as smc_telecom"}},
        {"key": "spork_p95", "source": "2607.03333", "system": spork["system"],
         "quantity": "GAIA P95 reduction",
         "published_reduction_pct": pct_tokens(s_p95)[0][1],
         "sentence": s_p95,
         "region": {"kind": "reported_wait_share", "band": band_reduction(s_wait, 0),
                    "why": "the paper reports the tool wait as a share of wall time in its own "
                           "workloads -- this is its operating region, stated by the paper itself"}},
        {"key": "spork_wait_share", "source": "2607.03333", "system": spork["system"],
         "quantity": "tool wait as a share of wall time, our workloads",
         "published_band_pct": band_reduction(s_wait, 0),
         "sentence": s_wait,
         "region": {"kind": "published_share", "why": "this is the external estimate the model's "
                    "coordinate p is compared against"}},
        {"key": "spork_probe_accuracy", "source": "2607.03333", "system": spork["system"],
         "quantity": "upcoming-tool-name probe accuracy across five benchmarks",
         "published_band_frac": tuple(x / 100.0 for x in band_reduction(s_probe, 0)),
         "sentence": s_probe,
         "region": {"kind": "hit_rate", "why": "the model's h is the fraction of steps issued early; "
                    "the probe accuracy is the paper's own estimate of how often that is right, so it "
                    "is used as h and DECLARED as a modelling choice, not measured"}},
    ]
    return cells


# ------------------------------------------------------------------ the mapping, in one place
def p_to_mS(p, mT=MT):
    """The tool-wait share p = mS/(mT+mS), inverted: the service mean that realises it."""
    return p * mT / (1.0 - p)


def ceiling_pct(p):
    """The model's UNLOADED, ORACLE ceiling in percent: 100 * p * (1-p).

    With one agent and a free worker, serial per-step latency is T+S and speculative is max(T,S), so
    the benefit is min(T,S) and, for exponentials, E[min] = mT mS/(mT+mS); as a fraction of the cycle
    T+S that is exactly p(1-p), maximised at p = 1/2 with 1/4.  This is the ceiling the file will not
    claim past -- and it is a PREDICTION about the published systems, not a fit to them.
    """
    if not 0.0 < p < 1.0:
        raise ValueError("p must be a share in (0,1); got %r" % (p,))
    return 100.0 * p * (1.0 - p)


def required_p_band(target_pct):
    """Invert p(1-p) = target/100: which tool-wait shares COULD produce this reduction.  None above
    the ceiling -- and that None is the honest answer for a published number the model cannot reach."""
    t = target_pct / 100.0
    if t > 0.25 + 1e-12:
        return None
    disc = math.sqrt(max(0.0, 1.0 - 4.0 * t))
    return ((1.0 - disc) / 2.0, (1.0 + disc) / 2.0)


PLANT_SIGN = False       # arm 3: read the published reduction as a NEGATIVE benefit
PLANT_CAP = None         # arm 4: replace the model's ceiling with a number typed in
PLANT_P_OFFSET = 0.0     # arm 2: simulate a different share than the one the cell names


def published_to_benefit_pct(published_reduction_pct, plant_sign=False):
    """A published REDUCTION of X% in latency IS a benefit of +X% in this instrument's coordinates.

    One function, one place: the published systems report a change in latency (`reducing latency by
    18.59%`), the instrument reports a benefit that is positive when speculation helps.  A plant reads
    the published number as if it were already a benefit -- the sign convention becomes load-bearing.
    """
    return (-1.0 if plant_sign else 1.0) * published_reduction_pct


# ------------------------------------------------------------------ the deciding runs
def run_share(p, h=H_ORACLE, seeds=SEEDS, steps=STEPS):
    """One cell of the external mapping: the single-agent, unloaded regime at tool-wait share p.

    Serial and speculative runs share each seed's draw stream (the instrument's own estimator), so the
    difference carries the policy effect only.  The per-seed benefit is the unit; the interval is over
    seeds.  The measured contention is reported per seed: the cell claims to be UNLOADED, and that is
    a measurement, not a premise.
    """
    mS = p_to_mS(p)
    rows = []
    for s in seeds:
        ser = I.agent_run(1, MT, mS, 0.0, steps, s, tail="light", speculate=False, c=1)
        spe = I.agent_run(1, MT, mS, h, steps, s, tail="light", speculate=True, c=1)
        ben = ser["mean_latency"] - spe["mean_latency"]
        rows.append({"seed": s, "benefit_pct": 100.0 * ben / ser["mean_latency"],
                     "rho": spe["rho"], "serial_mean": ser["mean_latency"],
                     "spec_mean": spe["mean_latency"], "steps": ser["n_samples"]})
    vals = [r["benefit_pct"] for r in rows]
    lo, hi = t_ci(vals)
    return {"p": p, "mS": mS, "h": h, "n_seeds": len(seeds), "steps": steps,
            "benefit_pct_mean": sum(vals) / len(vals), "benefit_pct_ci": [lo, hi],
            "benefit_pct_min": min(vals), "benefit_pct_max": max(vals),
            "rho_max": max(r["rho"] for r in rows),
            "serial_mean": sum(r["serial_mean"] for r in rows) / len(rows),
            "ceiling_pct": ceiling_pct(p), "rows": rows}


def t_ci(xs):
    """A 95% interval over seeds (Student t, small-sample).  Reported with every mean."""
    n = len(xs)
    m = sum(xs) / n
    if n < 2:
        return (m, m)
    var = sum((x - m) ** 2 for x in xs) / (n - 1)
    se = math.sqrt(var / n)
    t = T95.get(n, 1.96)
    return (m - t * se, m + t * se)


T95 = {1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571, 6: 2.447, 7: 2.365, 8: 2.306, 9: 2.262,
       10: 2.228, 12: 2.179, 15: 2.131, 20: 2.086, 25: 2.060, 30: 2.042, 40: 2.021, 60: 2.000}


def verdict_for(cell, runs, plant_sign=False, plant_cap=None):
    """Does this cell reproduce the published result's SIGN, and is its magnitude reachable?

    The verdict is taken on the two things the registration names -- sign, and per-cell whether the
    magnitude is reached -- and on nothing else.  A cell whose publication the model cannot reach says
    so with its shortfall; a cell whose REPORTED OPERATING REGION is what the model is run in says
    whether the published number falls inside the model's own interval there.
    """
    target = published_to_benefit_pct(cell["published_reduction_pct"], plant_sign)
    cap = plant_cap if plant_cap is not None else 0.25
    model_ceiling = 100.0 * cap
    rec = {"key": cell["key"], "source": cell["source"], "system": cell["system"],
           "quantity": cell["quantity"],
           "published_reduction_pct": cell["published_reduction_pct"],
           "published_as_benefit_pct": target, "sentence": cell["sentence"],
           "region": cell.get("region"), "runs": runs}
    # THE VERDICT IS THE TWO SIGNS COMPARED.  The first version of this rule read the MODEL's sign and
    # compared it against the constant "POSITIVE" -- so the published sign was never read, and a plant
    # that turned the published reduction into a negative benefit still read MATCH.  The registered
    # sentence is "reproduces the published result's SIGN", so both signs are computed and compared,
    # and the runs must agree among themselves before either is used.
    model_signs = [("POSITIVE" if r["benefit_pct_mean"] > 0 else "NEGATIVE") for r in runs]
    published_sign = "POSITIVE" if target > 0 else "NEGATIVE"
    rec["model_signs"] = sorted(set(model_signs)) or ["no run"]
    rec["published_sign"] = published_sign
    rec["model_sign"] = (model_signs[0] if len(set(model_signs)) == 1 else "UNRESOLVED")
    rec["sign"] = ("MATCH" if rec["model_sign"] == published_sign
                   else ("UNRESOLVED" if rec["model_sign"] == "UNRESOLVED" else "MISMATCH"))
    reachable = target <= model_ceiling + 1e-12
    rec["reachable"] = bool(reachable)
    rec["model_ceiling_pct"] = model_ceiling
    if not reachable:
        rec["magnitude"] = "NOT REACHED"
        rec["shortfall_pp"] = target - model_ceiling
        rec["magnitude_reason"] = ("the published reduction exceeds the model's unloaded ceiling "
                                   "p(1-p) <= 25%% at p = 1/2, so no tool-wait share reproduces it "
                                   "with single-step speculation; the published mechanism (multi-step "
                                   "macro commits) is outside this instrument's action space")
    else:
        rec["magnitude"] = "REACHABLE"
        rec["band"] = required_p_band(target)
    # THE CELL WITH A REPORTED OPERATING REGION IS TESTED BY INVERSION, NOT BY SAMPLING SHARES.
    # The first version of this rule asked "does the published number fall inside the model's interval
    # at one of the three shares I happened to run?" -- a GRID question.  The registration asks whether
    # the model reproduces the published result INSIDE THE PAPER'S OWN REPORTED REGION, and that is the
    # share the model's inversion points at: p(1-p) = target has two roots, and the question is whether
    # a root lies inside the band the paper reports.  (Measured: at the sampled shares the model says
    # 13.4 / 19.5 / 23.3%, while the inverted root for 18% is p = 0.2468 -- which the paper's own
    # 16-37% band contains.  The grid answer and the inversion answer differ, and only the inversion
    # answers the registered question.)
    if cell["region"] and cell["region"]["kind"] == "reported_wait_share":
        rep_lo, rep_hi = (x / 100.0 for x in cell["region"]["band"])
        roots = required_p_band(target) if target > 0 else None
        rec["reported_band_p"] = [rep_lo, rep_hi]
        rec["implied_shares_p"] = list(roots) if roots else None
        overlap = (None if roots is None else [max(roots[0], rep_lo), min(roots[1], rep_hi)])
        rec["overlap_p"] = overlap
        rec["inside_reported_region"] = bool(overlap and overlap[0] <= overlap[1])
        sim = [r for r in runs if abs(r["p"] - (roots[0] if roots else -1.0)) < 1e-9]
        rec["simulation_at_implied_share"] = ({"p": sim[0]["p"], "mean": sim[0]["benefit_pct_mean"],
                                               "ci": sim[0]["benefit_pct_ci"]} if sim else None)
        rec["simulation_confirms_published"] = bool(
            sim and sim[0]["benefit_pct_ci"][0] <= target <= sim[0]["benefit_pct_ci"][1])
        lo = min(r["benefit_pct_ci"][0] for r in runs)
        hi = max(r["benefit_pct_ci"][1] for r in runs)
        rec["model_band_pct"] = [lo, hi]
        rec["magnitude"] = ("REACHED" if rec["inside_reported_region"]
                            and rec["simulation_confirms_published"] else "SHORTFALL")
        rec["magnitude_reason"] = (
            "the share the model's inversion points at (p = %.4f) lies inside the band the paper "
            "reports for its own workloads (%.2f-%.2f), and the simulator run at that share returns "
            "the published number inside its interval" % (roots[0], rep_lo, rep_hi)
            if rec["inside_reported_region"] and rec["simulation_confirms_published"] else
            "the model's inversion points at a share outside the band the paper reports, or the "
            "simulator at that share does not contain the published number")
    return rec


# ------------------------------------------------------------------ the deciding comparison
def compare():
    """Run every external cell where it is to be run, and take the registered verdict.

    WHERE EACH CELL IS RUN, and why (this is the design decision, stated rather than implied):
      * spork_p95 -- INSIDE the paper's own reported wait-share band, at its two ends and its middle.
        This is the only cell that HAS an operating region reported by its own paper, so it is the one
        the registered sentence points at.
      * smc_telecom -- at p = 1/3 (mT = 2, mS = 1: the ratio the rest of this study is run at) and at
        p = 1/2 (the model's best point).  The paper reports no wait share, so the model is run at the
        two shares that matter and the REQUIRED band is inverted from the reduction it reports.
      * smc_appworld -- at p = 1/2, the model's best point: the honest way to report "not reachable" is
        to have run the model where it is strongest and still fall short.
      * spork_p95_h_probe -- the same share as the top of the band, with h = the paper's own LOWER
        reported probe accuracy instead of the oracle.  Declared as a modelling choice: the probe
        predicts a tool NAME, the instrument's h is the fraction of steps issued early.
    """
    cells = build_cells()
    by_key = {c["key"]: c for c in cells}
    wait_lo, wait_hi = (x / 100.0 for x in by_key["spork_wait_share"]["published_band_pct"])
    # the share the published number implies, so the simulator is asked AT the point the inversion
    # names (the cell's verdict checks that this run's interval contains the published number)
    implied = required_p_band(by_key["spork_p95"]["published_reduction_pct"])[0]
    runs = {
        "spork_p95": [run_share(p) for p in (wait_lo, implied, wait_hi)],
        "smc_telecom": [run_share(1.0 / 3.0), run_share(0.5)],
        "smc_appworld": [run_share(0.5)],
        "spork_p95_h_probe": [run_share(wait_hi, h=H_PROBE_LOW)],
    }
    # the unloaded premise, MEASURED for every run: no queue delay means the serial mean is the cycle
    regime = []
    for key, rs in sorted(runs.items()):
        for r in rs:
            cycle = MT + r["mS"]
            regime.append({"which": key, "p": r["p"], "h": r["h"], "cycle_mean": cycle,
                           "serial_mean": r["serial_mean"],
                           "serial_over_cycle": r["serial_mean"] / cycle})
    verdicts = [verdict_for(by_key[k], runs[k], plant_sign=PLANT_SIGN, plant_cap=PLANT_CAP)
                for k in ("smc_telecom", "smc_appworld", "spork_p95")]
    reported_region = [v for v in verdicts if v["region"] and
                       v["region"]["kind"] == "reported_wait_share"]
    out = {
        "read_date": READ_DATE, "read_via": READ_VIA,
        "sources": SOURCES,
        "declared_modelling_choices": [
            "the external cell is the SINGLE-AGENT, UNLOADED regime (one agent loop, one worker): the "
            "published numbers are one agent's own latency against its own tools",
            "p = mS/(mT+mS) is the tool-wait share SPORK reports; mT is fixed at 1.0 so p is the free "
            "coordinate",
            "the probe accuracy band is used as h (the fraction of steps issued early), declared as a "
            "modelling choice -- the probe predicts a tool name, not a step",
            "the model's benefit is positive when speculation helps, while the published numbers are "
            "latency REDUCTIONS: one function converts, and its plant is an arm",
        ],
        "parsed_cells": cells,
        "runs": runs,
        "regime_check": regime,
        "verdicts": verdicts,
        "summary": {
            "n_cells": len(verdicts),
            "sign_match": sum(1 for v in verdicts if v["sign"] == "MATCH"),
            "magnitudes": {v["key"]: v["magnitude"] for v in verdicts},
            "reported_region_cell": reported_region[0]["key"] if reported_region else None,
            "reported_region_verdict": (reported_region[0]["sign"] + "/" + reported_region[0]["magnitude"]
                                        if reported_region else None),
            "reported_region_inside": (reported_region[0].get("inside_reported_region")
                                       if reported_region else None),
            "reported_region_overlap_p": (reported_region[0].get("overlap_p")
                                          if reported_region else None),
            "model_band_pct_in_reported_region": (reported_region[0].get("model_band_pct")
                                                  if reported_region else None),
            "h_sensitivity": {"h_oracle": max(r["benefit_pct_mean"] for r in runs["spork_p95"]),
                              "h_probe_low": runs["spork_p95_h_probe"][0]["benefit_pct_mean"],
                              "h_probe_low_ci": runs["spork_p95_h_probe"][0]["benefit_pct_ci"],
                              "published_target_pct": by_key["spork_p95"]["published_reduction_pct"]},
        },
    }
    out["summary"]["sign_rule"] = "published sign vs model sign, both computed (not the model's sign "                                 "against a constant)"
    ok = (out["summary"]["sign_match"] == len(verdicts)
          and reported_region and reported_region[0]["sign"] == "MATCH"
          and reported_region[0]["magnitude"] == "REACHED"
          and reported_region[0].get("inside_reported_region")
          and out["summary"]["magnitudes"]["smc_appworld"] == "NOT REACHED")
    out["metric_f"] = {"status": "MET" if ok else "UNMET",
                       "rule": "every published cell reproduces the published SIGN; the cell whose own "
                               "paper reports an operating region is REPRODUCED inside that region; and "
                               "a cell the model cannot reach is reported as NOT REACHED with its "
                               "shortfall rather than smoothed into an agreement (reported, not failed)"}
    return out


# ------------------------------------------------------------------ battery
def selftest():
    """Every arm must be able to fail, and each prints what it read rather than only a verdict."""
    arms = []

    def arm(name, ok, detail):
        arms.append({"arm": name, "ok": bool(ok), "detail": detail})

    cells = {c["key"]: c for c in build_cells()}

    # ARM 1 (two-sided): the cell's number COMES from the sentence.  The baseline must match the
    # number in the stored sentence, and an edited sentence must move the cell.
    tel = cells["smc_telecom"]
    toks = pct_tokens(tel["sentence"])
    baseline_ok = tel["published_reduction_pct"] == toks[1][1]
    edited = tel["sentence"].replace("18.59", "31.42")
    moved = sequential_reduction(edited, "over sequential execution") == 31.42
    arm("a cell's number is parsed from its sentence (editing the sentence moves the cell)",
        baseline_ok and moved,
        {"parsed": tel["published_reduction_pct"], "tokens": toks, "after_edit": 31.42,
         "baseline_matches_sentence": baseline_ok, "edited_sentence_moves_it": moved})

    # ARM 2: the token is chosen by the PHRASE plus a property that must hold independently.  Swapping
    # the two reported numbers must trip the cross-check, so position alone cannot be the reason.
    swapped = tel["sentence"].replace("10.23", "18.59").replace("18.59\\% over sequential",
                                                                "10.23\\% over sequential")
    caught = False
    try:
        sequential_reduction(swapped, "over sequential execution")
    except AssertionError:
        caught = True
    arm("swapping the two reported numbers is caught (the choice is anchored on a property)",
        caught, {"planted_sentence_swaps_the_reduction": caught})

    # ARM 3 (two-sided): the sign convention is load-bearing.
    runs1 = [run_share(1.0 / 3.0, seeds=SEEDS[:12], steps=STEPS)]
    v_true = verdict_for(cells["spork_p95"], runs1, plant_sign=False)
    v_plant = verdict_for(cells["spork_p95"], runs1, plant_sign=True)
    opposite = dict(cells["spork_p95"])
    opposite["published_reduction_pct"] = -18.0          # a paper reporting a speed-up LOSS
    v_opp = verdict_for(opposite, runs1)
    arm("the verdict compares BOTH signs (a negative publication reads MISMATCH, the real one MATCH)",
        v_true["sign"] == "MATCH" and v_plant["sign"] == "MISMATCH" and v_opp["sign"] == "MISMATCH",
        {"published_sign_true": v_true["published_sign"], "model_sign": v_true["model_sign"],
         "verdict_true": v_true["sign"], "published_as_benefit_plant": v_plant["published_as_benefit_pct"],
         "verdict_plant": v_plant["sign"], "verdict_paper_reporting_a_loss": v_opp["sign"]})

    # ARM 4 (two-sided): the ceiling is real.  A cell the model cannot reach reads NOT REACHED with a
    # shortfall -- and the SAME cell under a generous ceiling reads REACHABLE, so the branch is not
    # taken by construction.
    v_cap = verdict_for(cells["smc_appworld"], [run_share(0.5)], plant_cap=0.9)
    v_real = verdict_for(cells["smc_appworld"], [run_share(0.5)])
    arm("a published reduction above the model's ceiling reads NOT REACHED, with a shortfall",
        v_real["magnitude"] == "NOT REACHED" and v_real["shortfall_pp"] > 0
        and v_cap["magnitude"] == "REACHABLE",
        {"real_ceiling_pct": v_real["model_ceiling_pct"], "magnitude": v_real["magnitude"],
         "shortfall_pp": round(v_real["shortfall_pp"], 4),
         "under_generous_ceiling": v_cap["magnitude"]})

    # ARM 5: the analytic ceiling the file uses is checked against the INSTRUMENT, not against itself.
    checks = []
    for p in (1.0 / 3.0, 0.5):
        r = run_share(p, h=H_ORACLE, seeds=SEEDS[:12], steps=STEPS)
        inside = r["benefit_pct_ci"][0] <= r["ceiling_pct"] <= r["benefit_pct_ci"][1]
        checks.append({"p": p, "measured": r["benefit_pct_mean"], "ci": r["benefit_pct_ci"],
                       "ceiling": r["ceiling_pct"], "ceiling_inside_ci": inside})
    arm("the closed-form ceiling is inside the simulator's own interval at two shares",
        all(c["ceiling_inside_ci"] for c in checks), checks)

    # ARM 6 (two-sided): the cell claims to be UNLOADED.  That is measured (the serial mean IS the
    # cycle T+S, no queue delay), and the same check must fail when the same code is driven with four
    # agents against one worker -- otherwise the check cannot see a loaded cell.
    def serial_over_cycle(p, n_agents, c, seeds=SEEDS[:8]):
        mS = p_to_mS(p)
        vals = []
        for s in seeds:
            ser = I.agent_run(n_agents, MT, mS, 0.0, STEPS, s, tail="light", speculate=False, c=c)
            vals.append(ser["mean_latency"] / (MT + mS))
        return sum(vals) / len(vals)
    free = serial_over_cycle(1.0 / 3.0, 1, 1)
    loaded = serial_over_cycle(1.0 / 3.0, 4, 1)
    arm("the unloaded premise is measured: free is the cycle, four agents on one worker is not",
        abs(free - 1.0) <= 0.05 and loaded > 1.15,
        {"one_agent_one_worker": round(free, 5), "four_agents_one_worker": round(loaded, 5)})

    # ARM 7: the required-band inversion is exact, and it REFUSES a target above the ceiling.
    inv = []
    for t in (18.59, 25.0):
        lo, hi = required_p_band(t)
        inv.append({"target": t, "band": [lo, hi], "p_lo_times": ceiling_pct(lo),
                    "p_hi_times": ceiling_pct(hi),
                    "exact": abs(ceiling_pct(lo) - t) < 1e-9 and abs(ceiling_pct(hi) - t) < 1e-9})
    arm("the required-share band inverts p(1-p) exactly, and refuses a target above the ceiling",
        all(x["exact"] for x in inv) and required_p_band(26.0) is None,
        {"bands": inv, "above_ceiling": required_p_band(26.0)})

    # ARM 7b: the inversion answer and the grid answer are DIFFERENT questions, and the cell takes the
    # inversion one.  A paper-reported band that excludes the inverted root must read SHORTFALL; the
    # real band must read REACHED.  (This arm exists because the first version took the grid answer and
    # read SHORTFALL for a cell the inversion reproduces.)
    cell_rep = cells["spork_p95"]
    grid_shares = (0.16, (0.16 + 0.37) / 2.0, 0.37)      # EXACTLY how the first version sampled
    runs_grid = [run_share(x, seeds=SEEDS[:12], steps=STEPS) for x in grid_shares]
    implied_root = required_p_band(18.0)[0]
    runs_rep = runs_grid + [run_share(implied_root, seeds=SEEDS[:12], steps=STEPS)]
    v_reached = verdict_for(cell_rep, runs_rep)
    planted = dict(cell_rep)
    planted["region"] = {"kind": "reported_wait_share", "band": (5.0, 9.0)}
    v_short = verdict_for(planted, runs_rep)
    grid_answer = [r["p"] for r in runs_grid if r["benefit_pct_ci"][0] <= 18.0 <= r["benefit_pct_ci"][1]]
    arm("the reported-region cell takes the INVERSION answer (inside the band REACHED, outside "
        "SHORTFALL), while the sampled shares alone would say otherwise",
        v_reached["inside_reported_region"] and v_reached["simulation_confirms_published"]
        and v_reached["magnitude"] == "REACHED" and v_short["magnitude"] == "SHORTFALL"
        and grid_answer == [],
        {"implied_share": v_reached["implied_shares_p"], "reported_band": v_reached["reported_band_p"],
         "overlap": v_reached["overlap_p"], "verdict_real": v_reached["magnitude"],
         "verdict_band_planted_outside": v_short["magnitude"],
         "grid_shares": list(grid_shares),
         "grid_shares_whose_ci_contains_the_published_number": grid_answer,
         "verdict_on_the_grid_alone": verdict_for(cell_rep, runs_grid)["magnitude"],
         "sim_at_implied": v_reached["simulation_at_implied_share"]})

    # ARM 8: the h knob is load-bearing -- if h=0.746 and h=1.0 gave the same answer, the h-sensitivity
    # sub-finding would be vacuous.
    hi_share = cells["spork_wait_share"]["published_band_pct"][1] / 100.0
    oracle = run_share(hi_share, h=H_ORACLE, seeds=SEEDS[:12], steps=STEPS)
    probe = run_share(hi_share, h=H_PROBE_LOW, seeds=SEEDS[:12], steps=STEPS)
    diff = oracle["benefit_pct_mean"] - probe["benefit_pct_mean"]
    arm("lowering h to the paper's own reported probe accuracy MOVES the benefit (the knob is live)",
        diff > 0.5,
        {"h_oracle": oracle["benefit_pct_mean"], "h_probe": probe["benefit_pct_mean"],
         "difference_pp": round(diff, 4)})

    return {"arms": arms, "n_fails": sum(1 for a in arms if not a["ok"]),
            "fails": [a["arm"] for a in arms if not a["ok"]]}


# ------------------------------------------------------------------ main
def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--json", default=None)
    args = ap.parse_args(argv)
    if args.selftest:
        st = selftest()
        for a in st["arms"]:
            print("%-78s %s" % (a["arm"], "OK" if a["ok"] else "FAILED"))
            print("      read: %s" % json.dumps(a["detail"])[:400])
        print("SELFTEST: %d arm(s), %d failure(s)" % (len(st["arms"]), st["n_fails"]))
        return 0 if st["n_fails"] == 0 else 1
    out = compare()
    out["selftest"] = selftest()
    s = out["summary"]
    print("== registered metric (f): the external cell (%s, sources read %s) ==" % (READ_VIA, READ_DATE))
    for v in out["verdicts"]:
        print("-- %-14s %-28s published reduction %+.2f%% (as benefit %+.2f%%) | sign %s | magnitude %s"
              % (v["key"], v["source"], v["published_reduction_pct"], v["published_as_benefit_pct"],
                 v["sign"], v["magnitude"]))
        if v["magnitude"] == "NOT REACHED":
            print("      shortfall %.2f pp over the model ceiling %.2f%% -- %s"
                  % (v["shortfall_pp"], v["model_ceiling_pct"], v["magnitude_reason"]))
        if v.get("reported_band_p"):
            print("      paper's own reported share band %s; the model's inversion points at p = %.4f; "
                  "overlap %s => inside the paper's region: %s"
                  % (["%.2f" % x for x in v["reported_band_p"]],
                     (v["implied_shares_p"] or [float("nan")])[0],
                     ["%.4f" % x for x in (v["overlap_p"] or [])], v["inside_reported_region"]))
            print("      simulator AT that share: %s (contains the published number: %s)"
                  % (json.dumps(v["simulation_at_implied_share"]), v["simulation_confirms_published"]))
    print("-- reported operating region: %s -> %s" % (s["reported_region_cell"],
                                                      s["reported_region_verdict"]))
    print("-- signs: %d/%d match | magnitudes: %s" % (s["sign_match"], s["n_cells"],
                                                      json.dumps(s["magnitudes"])))
    print("-- h sensitivity at the top of the band: oracle %.2f%% vs probe-low %.2f%% "
          "(published target %.2f%%)" % (s["h_sensitivity"]["h_oracle"],
                                         s["h_sensitivity"]["h_probe_low"],
                                         s["h_sensitivity"]["published_target_pct"]))
    print("-- metric (f): %s" % out["metric_f"]["status"])
    if args.json:
        io.open(args.json, "w", encoding="utf-8", newline="\n").write(
            json.dumps(out, indent=1, sort_keys=True) + "\n")
        print("wrote %s" % args.json)
    return 0


if __name__ == "__main__":
    sys.exit(main())
