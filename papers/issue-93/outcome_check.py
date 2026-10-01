#!/usr/bin/env python3
"""#93 R420 -- the per-prior `Outcome` rows, with an owner for every number they state.

WHY THIS FILE EXISTS.  The registration's Outcome section is the study's *promise kept*: for each of PB1-PB4 it
must say whether the results confirm the prior, contradict it, or leave it unresolved.  A row like that is a
claim about instruments, and this study's own rule (learned the hard way in #87) is that **a claim with no owner
drifts**: the instrument that produced a number is the only thing that can say whether the row still states it.
So the rows live in `outcomes.md` with their numbers in one fenced block, and this file OWNS that block:

  * every quantity is **recomputed from the instruments** (the exact enumeration and the closed forms are
    imported, never copied) or **read from the instrument's own committed record** -- never re-typed;
  * `--emit` prints the block, so the document's numbers are produced by the computation rather than typed
    beside it, and `--write-doc` places the block into `outcomes.md`;
  * the default run compares the document's block against the computation and fails on any disagreement;
  * it also checks the thing a grade of a prior can get wrong silently: **the prior text the row scores is the
    registered text** -- every quoted clause must appear verbatim in the stored extract of the issue body
    (`registration_priors.md`), so a re-worded prior cannot be scored as the registered one.

WHAT EACH ROW READS, AND WHERE ITS VERDICT COMES FROM.  The verdicts are the instruments' recorded readings; the
computation below re-derives the decisive numbers so the row cannot drift from them:

  PB1  the coverage clause is read from v1's curvature and sign law + v0's screening slope, and its accuracy
       clause from the enumeration's own derivative in `a` at both ends of the fidelity axis.  The registration's
       **second clause is stated in the direction opposite to its own gloss**, so BOTH readings are scored and
       both are reported (`pb1_accuracy_clause_readings`).
  PB2  the registration's *own success metric (b)* -- `(dE/da)/(dE/db)` at `b in {0, 0.5, 1}` -- from v4's
       record, re-derived from v0's enumeration with the same one-sided/central rule; plus the crossover.
  PB3  the affineness (v1's curvature), the sign law, and the fatigue vertex (v1's `P5_fatigue`); the literal
       "escalate more" clause is scored at both ends of the fidelity axis.
  PB4  v2's design ladder, its per-class value decomposition, the published anchor reproduction, and v3's
       headline sensitivity + external-validation arm.

Usage:
  python3 outcome_check.py                verify outcomes.md against the instruments   (exit 0 = agree)
  python3 outcome_check.py --emit         print the readings block as computed
  python3 outcome_check.py --write-doc    replace the block inside outcomes.md with the computed one
  python3 outcome_check.py --selftest     the battery: mutate the document, the prior text and the records
Exit: 0 = agree | 1 = the document and the instruments disagree | 2 = NOT RUN (a record or instrument is missing).
"""
import importlib.util
import io
import json
import os
import re
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
DOC = os.path.join(HERE, "outcomes.md")
PRIORS = os.path.join(HERE, "registration_priors.md")
RECORDS = {name: os.path.join(HERE, "gate_%s_results.json" % name)
           for name in ("v0", "v1", "v2", "v3", "v4", "v5", "v6")}
BEGIN = "<!-- readings:begin -->"
END = "<!-- readings:end -->"


def load(name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(HERE, name + ".py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)          # the instruments are IMPORTED: one owner for every formula
    return mod


V0 = load("gate_v0")
V1 = load("gate_v1")


def records():
    return {k: json.load(io.open(p, encoding="utf-8")) for k, p in RECORDS.items()}


def v_of(params, variant, b, s):
    """V(s) = E0 - E1 from v0's EXACT enumeration.  The guard is lifted (`screen_only=False`) because this
    function is asked about b < 1 as well; at b = 1 the lifted route is the same model (v1's P6 continuity
    control measured worst |v1 - v0| = 0.0 over 12 reads at b = 1)."""
    loss, _ = V0.enumerate_exact(params, s, variant=variant, b=b, screen_only=False)
    return params["L"] * params["pi"] - loss


def _loss_at(params, variant, b, a):
    loss, _ = V0.enumerate_exact(dict(params, a=a), 1.0, variant=variant, b=b, screen_only=False)
    return loss


def dE_da(params, b, h=1e-4):
    """d(under-gate expected loss)/da at s = 1 (PB3's own rule), from the enumeration.  Central inside the
    axis, one-sided (forward) at b = 0, where a central difference would step outside it."""
    if b <= 0.0:
        return (_loss_at(params, "mismatch", 0.0, params["a"] + h) - _loss_at(params, "mismatch", 0.0, params["a"])) / h
    return (_loss_at(params, "mismatch", b, params["a"] + h)
            - _loss_at(params, "mismatch", b, params["a"] - h)) / (2 * h)


def axis_ratio(params, variant, b, h=1e-4):
    """The registration's metric (b): (dE/da)/(dE/db), with the rule v4 declared and this file re-derives from
    the enumeration -- forward at b = 0, central inside the axis, backward at b = 1.  The record is cross-checked
    against this, never trusted for it."""
    if 0.0 < b < 1.0:
        denom = (_loss_at(params, variant, b + h, params["a"])
                 - _loss_at(params, variant, b - h, params["a"])) / (2 * h)
    elif b >= 1.0:
        denom = (_loss_at(params, variant, b, params["a"])
                 - _loss_at(params, variant, b - h, params["a"])) / h
    else:
        denom = (_loss_at(params, variant, b + h, params["a"])
                 - _loss_at(params, variant, b, params["a"])) / h
    num = (_loss_at(params, variant, b, params["a"] + h)
           - _loss_at(params, variant, b, params["a"] - h)) / (2 * h)
    return (num / denom) if denom else float("inf")


def compute():
    """The truth: every number the Outcome rows state, computed or read at its object."""
    rec = records()
    base = dict(V0.DEFAULT)                     # pi, a, f, L, c, cb, eta at the registered defaults
    t = {}

    # ---- PB1: clause 1 -- is the gate's harm non-increasing in coverage?  (affine => the slope decides)
    t["pb1_curvature_worst_relative"] = rec["v1"]["curvature"]["worst_relative"]
    t["pb1_curvature_cells"] = rec["v1"]["curvature"]["n"]
    t["pb1_slope_at_b1"] = round(V1.slope_closed(base, "none", 1.0), 6)
    t["pb1_bstar_mismatch"] = round(rec["v1"]["thresholds"]["mismatch"], 4)
    t["pb1_bstar_substitution"] = round(rec["v1"]["thresholds"]["substitution"], 4)
    t["pb1_slope_mismatch_at_b0"] = round(V1.slope_closed(base, "mismatch", 0.0), 6)
    # The clause's own two-sided check.  NOTE what the first version of this property got wrong: it asserted
    # the COVERAGE SLOPE changes sign at each channel's `b*`, and the computation said no.  It is true for a
    # misrepresenting channel (`V(0) = 0` there, so `V(1)` IS the slope) and false for a laundering one, whose
    # `b*` is where the gate's BEST value crosses zero -- the additive laundering term keeps the slope positive
    # for a stretch of the axis in between.  The slope's own zero is a DIFFERENT number for that channel, and the
    # instruments name it: it is the `eta = 0` sign-law threshold, which v1 also found to be the fatigue floor.
    # So the property is stated per channel, and the body below checks each sign against its own threshold.
    t["pb1_slope_threshold_mismatch"] = round(rec["v1"]["thresholds"]["mismatch"], 6)
    t["pb1_slope_threshold_substitution"] = round(rec["v1"]["P5_fatigue"]["sign_law_bstar_eta0"], 6)
    t["pb1_value_threshold_substitution"] = round(rec["v1"]["thresholds"]["substitution"], 4)
    t["pb1_laundering_has_two_thresholds"] = bool(
        abs(t["pb1_value_threshold_substitution"] - t["pb1_slope_threshold_substitution"]) > 0.1)
    sign_ok = True
    for variant, thr in (("mismatch", t["pb1_slope_threshold_mismatch"]),
                         ("substitution", t["pb1_slope_threshold_substitution"])):
        for b in V1.B_GRID:
            sl = V1.slope_closed(base, variant, b)
            if b < thr - 1e-6 and sl >= 0:
                sign_ok = False
            if b > thr + 1e-6 and sl <= 0:
                sign_ok = False
    t["pb1_slope_sign_follows_its_own_threshold"] = bool(sign_ok)
    t["pb1_substitution_harmful_at_zero_coverage_below_1"] = bool(
        all(V1.value_closed(base, "substitution", b, 0.0) < 0 for b in V1.B_GRID if b < 1.0)
        and abs(V1.value_closed(base, "substitution", 1.0, 0.0)) < 1e-15)

    # ---- PB1: clause 2 -- the accuracy axis, at both ends of the fidelity axis
    t["pb1_dEda_at_b1"] = round(dE_da(base, 1.0), 6)
    t["pb1_dEda_at_b0"] = round(dE_da(base, 0.0), 12)

    # ---- PB2: the registration's metric (b), cross-checked record vs recomputation.  The record states the
    # b = 0 cells in the A2 check's ratio list (the b = 0.5 / 1.0 cells also have their own verdict entries and
    # their `accuracy_pays_more` flags); both places are read so neither can drift from the other.
    a2 = {c["id"]: c for c in rec["v4"]["checks"]}["A2-declared-vs-measured-axis"]["per_variant"]
    for variant in ("mismatch", "substitution"):
        for idx, b in enumerate((0.0, 0.5, 1.0)):
            rec_v = a2[variant]["ratios"][idx]
            t["pb2_%s_at_b%s_record" % (variant, b)] = None if rec_v is None else round(rec_v, 6)
            t["pb2_%s_at_b%s_recomputed" % (variant, b)] = round(axis_ratio(base, variant, b), 6)
    t["pb2_crossover_stated"] = round(rec["v4"]["default"]["a"] - rec["v4"]["default"]["f"], 6)
    # The registered fidelity SET is a fact of the registration, and the predicted crossing for a laundering
    # channel is a refusal the instrument states -- both are stated in the rows, so both get an owner.
    for nm, val in (("low", 0.0), ("mid", 0.5), ("high", 1.0)):
        t["pb2_registered_b_%s" % nm] = val
    fc = [c for c in rec["v4"]["checks"] if c["id"] == "F-crossover"][0]
    t["pb2_crossover_predicted_laundering"] = round(fc["cross"]["substitution"]["predicted"], 2)
    t["pb2_crossover_deviation"] = float(
        [c for c in rec["v4"]["checks"] if c["id"] == "F-crossover"][0]["cross"]["mismatch"]["deviation"])
    t["pb2_accuracy_pays_more_at_b1_mismatch"] = bool(
        rec["v4"]["pb2_verdict"]["mismatch"]["1.0"]["accuracy_pays_more"])
    t["pb2_accuracy_pays_more_at_b05_mismatch"] = bool(
        rec["v4"]["pb2_verdict"]["mismatch"]["0.5"]["accuracy_pays_more"])

    # ---- PB3: affineness, the literal clause at both ends, and the fatigue mechanism
    t["pb3_affine_worst_relative"] = rec["v1"]["curvature"]["worst_relative"]
    t["pb3_all_corners"] = bool(rec["v1"]["P5_fatigue"]["kappa0_all_corner"])
    t["pb3_fatigue_interior_above_floor"] = bool(rec["v1"]["P5_fatigue"]["kappa1_interior_above_floor"])
    t["pb3_b_floor_closed"] = round(rec["v1"]["P5_fatigue"]["b_floor_closed"], 6)
    t["pb3_floor_equals_sign_law_eta0"] = bool(rec["v1"]["P5_fatigue"]["floor_matches_sign_law"])
    t["pb3_fatigue_cells_above"] = int(rec["v1"]["P5_fatigue"]["n_above"])
    t["pb3_fatigue_cells_below"] = int(rec["v1"]["P5_fatigue"]["n_below"])
    t["pb3_grid_vs_closed"] = float(rec["v1"]["P5_fatigue"]["worst_grid_vs_closed"])
    t["pb3_fatigue_grid_step"] = float(rec["v1"]["P5_fatigue"]["grid_step"])

    # ---- PB4: the design ladder, its decomposition, the anchor, the headline
    t["pb4_check_value_per_unit_sigma_v"] = round(rec["v2"]["P2_check_value"]["rows"][2]["gain"] /
                                                 rec["v2"]["P2_check_value"]["rows"][2]["sigma_v"], 6)
    t["pb4_blind_spot_per_unit_sigma_i"] = round(rec["v2"]["P3_blind_spot"]["rows"][2]["gap"] /
                                                 rec["v2"]["P3_blind_spot"]["rows"][2]["sigma_i"], 6)
    t["pb4_display_residual_at_delta_030"] = float(rec["v2"]["P4_display_blind"]["rows"][2]["gap"])
    t["pb4_display_residual_per_unit_delta"] = round(rec["v2"]["P4_display_blind"]["rows"][2]["gap"] /
                                                      rec["v2"]["P4_display_blind"]["rows"][2]["delta"], 6)
    t["pb4_attack_success_same_R_check"] = round(rec["v2"]["P5_ordering"]["attack_success"]["D3"], 4)
    t["pb4_attack_success_rederived_check"] = round(rec["v2"]["P5_ordering"]["attack_success"]["D4"], 4)
    t["pb4_attack_success_unbound"] = round(rec["v2"]["P5_ordering"]["attack_success"]["D1"], 4)
    t["pb4_designs_below_no_gate"] = int(len(rec["v2"]["P5_ordering"]["gate_worse_than_no_gate"]))
    t["pb4_anchor_published_zero_reproduced"] = bool(
        rec["v2"]["P6_anchor"][0]["D3"] == 0.0 and rec["v2"]["P6_anchor"][0]["D4"] == 0.0)
    # The prose quotes the anchor's degradation points ("0.25 at one-tenth invisible, 0.5 at half") and the
    # published band ("inside the published 0.68-1.00 band"), so each of those numbers is read at the row that
    # holds it.  The rows are named by their LABEL, never by index, so a reordered record cannot silently shift
    # which row a quoted number belongs to.
    _anchor = {r["label"]: r for r in rec["v2"]["P6_anchor"]}
    _ten = [r for k, r in _anchor.items() if k.startswith("10%")][0]
    _half = [r for k, r in _anchor.items() if k.startswith("half")][0]
    t["pb4_anchor_degradation_10pct"] = round(_ten["D3"], 6)
    t["pb4_anchor_degradation_50pct"] = round(_half["D3"], 6)
    t["pb4_anchor_degradation_matches_sigma_share"] = bool(
        all(r["D3_matches_sigma_share"] for r in rec["v2"]["P6_anchor"]))
    _band = rec["v3"]["external"]["attack_band"]
    t["pb4_published_band_low"] = round(_band["published"][0], 6)
    t["pb4_published_band_high"] = round(_band["published"][1], 6)
    t["pb4_published_band_contains_unbound"] = bool(_band["inside"])
    t["pb4_d4_residual_classes"] = int(len(rec["v2"]["residual_channel"]["D4"]))
    t["pb4_headline_harmful_readings"] = int(rec["v3"]["headline_sensitivity"]["harmful_readings"])
    t["pb4_headline_readings"] = int(rec["v3"]["headline_sensitivity"]["readings"])
    t["pb4_headline_cells"] = int(len(rec["v3"]["headline_sensitivity"]["cells_with_a_harmful_gate"]))
    t["pb4_headline_designs"] = int(len(rec["v3"]["headline_sensitivity"]["designs_harmful_somewhere"]))
    t["pb4_headline_min_margin"] = round(rec["v3"]["headline_sensitivity"]["min_margin_frac"], 6)
    t["external_vac_beats_text"] = bool(rec["v3"]["external"]["vac_holds_in_every_cell"])
    t["external_coverage_rate"] = round(rec["v3"]["coverage"]["rate"], 6)
    t["external_coverage_n"] = int(rec["v3"]["coverage"]["readings"])

    # ---- metric (a): the boundary WITH AN INTERVAL (v5).  The registration asks for the boundary "with
    # bootstrap CIs"; v1 owns the exact point, and these are the interval's own numbers -- its calibration, its
    # precision law, its scaling, the slope test's size measured on a real null, and the two default-cell
    # intervals a row quotes.  Read at the record, never re-typed.
    v5 = rec["v5"]
    cal = v5["C7_calibration"]
    t["a_interval_denominator"] = int(cal["denominator"])
    t["a_interval_covered_fieller"] = int(cal["fieller_covered"])
    t["a_interval_rate_fieller"] = round(cal["fieller_rate"], 6)
    t["a_interval_rate_bootstrap"] = round(cal["bootstrap_rate"], 6)
    t["a_interval_excluded_out_of_axis"] = int(cal["n_out_of_axis_excluded"])
    t["a_interval_no_target"] = int(cal["n_no_target"])
    t["a_interval_nominal"] = round(v5["nominal"], 4)
    t["a_interval_wilson_lo"] = round(cal["fieller_wilson"][0], 4)
    t["a_interval_wilson_hi"] = round(cal["fieller_wilson"][1], 4)
    for _sr in v5["C5_scaling"]["rows"]:
        t["a_scaling_ratio_%s" % _sr["channel"]] = round(_sr["ratio"], 4)
    t["a_width_law_worst_dev_in_regime"] = round(v5["C4_width_law"]["worst_dev_in_regime"], 6)
    t["a_width_law_regime"] = round(v5["C4_width_law"]["slope_regime"], 4)
    t["a_scaling_worst_dev"] = round(v5["C5_scaling"]["worst_dev"], 6)
    t["a_null_rejections"] = int(v5["C6_states"]["null_for_the_slope_test"]["false_positives"])
    t["a_null_denominator"] = int(v5["C6_states"]["null_for_the_slope_test"]["denominator"])
    t["a_null_rate"] = round(v5["C6_states"]["null_for_the_slope_test"]["rate"], 6)
    t["a_estimator_worst_dev"] = round(v5["C2_estimator"]["worst_abs_dev"], 6)
    t["a_estimator_worst_width"] = round(v5["C2_estimator"]["worst_interval_width"], 6)
    t["a_mapping_worst_se"] = round(v5["C1_mapping"]["worst_z"], 4)
    t["a_states_bounded"] = int(v5["state_counts"].get("bounded", 0))
    t["a_states_flat"] = int(v5["state_counts"].get("flat", 0))
    _def = {(r["cell"], r["channel"]): r for r in v5["readings"] if r["family"] == "adjacent"}
    for _ch in ("mismatch", "substitution"):
        _r = _def[("defaults", _ch)]
        t["a_defaults_%s_exact" % _ch] = round(_r["exact_b_star"], 4)
        t["a_defaults_%s_lo" % _ch] = round(_r["fieller"]["lo"], 4)
        t["a_defaults_%s_hi" % _ch] = round(_r["fieller"]["hi"], 4)
        t["a_defaults_%s_width" % _ch] = round(_r["fieller"]["width"], 4)

    # ---- metric (a), second clause: the dependence on L/c (v6).  The clause sits inside a metric registered
    # "with bootstrap CIs", so the sweep's own numbers are owned here too: the two limits, the two windows, the
    # crossover with its closed form, the measured 1/R rate, and the two hidden parameters the C6 controls move.
    v6 = rec["v6"]
    lim = v6["limits"]
    t["a_rc_limit_mismatch"] = round(lim["mismatch_limit"], 6)
    t["a_rc_limit_substitution"] = round(lim["substitution_limit"], 6)
    t["a_rc_R_zero_mismatch"] = round(lim["mismatch_R_zero"], 4)
    t["a_rc_window_substitution"] = round(lim["substitution_denominator_zero"], 4)
    t["a_rc_Rc"] = round(v6["C5_crossover"]["R_c_closed"], 4)
    t["a_rc_Rc_closed_vs_bisected"] = float(v6["C5_crossover"]["closed_vs_bisected"])
    t["a_rc_bar_at_Rc_mismatch"] = round(v6["C5_crossover"]["b_mismatch_at_R_c"], 12)
    t["a_rc_bar_at_Rc_substitution"] = round(v6["C5_crossover"]["b_substitution_at_R_c"], 12)
    t["a_rc_sweep_readings"] = int(v6["C1_law"]["n_readings"])
    t["a_rc_sweep_checked"] = int(v6["C1_law"]["n_checked"])
    t["a_rc_sweep_skipped"] = int(v6["C1_law"]["n_skipped"])
    # BOTH channels' ladders are owned here: the row quotes each channel's rate, and a check that owned only one
    # would leave the other's quoted number unbacked -- the two ladders are also the only set-valued quantities in
    # the truth object, so they are the reason `numeric_vals` flattens a sequence at all.
    t["a_rc_rate_ratios"] = [round(r, 4) for r in v6["C3_rate"]["mismatch"]["differences_ratio"]]
    t["a_rc_rate_ratios_substitution"] = [round(r, 4) for r in v6["C3_rate"]["substitution"]["differences_ratio"]]
    t["a_rc_interval_covered"] = int(v6["C7_interval"]["n_covering"])
    t["a_rc_interval_n"] = int(v6["C7_interval"]["n"])
    _om = v6["C6_omissions"]
    t["a_rc_t_moves_mismatch"] = round(max(x["moved"]["mismatch"] for x in _om["limb_t"]), 6)
    t["a_rc_eta_moves_substitution"] = round(max(x["moved"]["substitution"] for x in _om["limb_eta"]), 6)
    t["a_rc_eta_moves_mismatch"] = round(max(x["moved"]["mismatch"] for x in _om["limb_eta"]), 6)
    t["a_rc_s_moves_substitution"] = round(max(x["moved"]["substitution"] for x in _om["limb_s"]), 6)
    t["a_rc_s_moves_mismatch"] = round(max(x["moved"]["mismatch"] for x in _om["limb_s"]), 6)
    t["a_rc_second_route_worst"] = float(v6["C1_law"]["worst_abs_diff"])
    return t


def block(truth):
    return BEGIN + "\n```json\n" + json.dumps(truth, indent=1, sort_keys=True) + "\n```\n" + END


def read_doc(path=DOC):
    """Read a document's readings block.  An unreadable block is a Fault, reported as a defect of the document
    -- not a traceback: a document that cannot be read has not been checked, and the two must not look alike."""
    return read_text(io.open(path, encoding="utf-8").read())


def read_text(txt):
    """The one reader.  `read_doc` is this applied to a path; the battery reads its plants through this too, so a
    plant cannot pass by being read by a different reader than the check uses."""
    if BEGIN not in txt or END not in txt:
        return txt, Fault("the document carries no readings block (markers %r / %r absent)" % (BEGIN, END))
    inner = txt.split(BEGIN, 1)[1].split(END, 1)[0]
    m = re.search(r'```json\n(.*?)\n```', inner, re.S)
    if not m:
        return txt, Fault("the readings block holds no json fence")
    try:
        return txt, json.loads(m.group(1))
    except ValueError as exc:
        return txt, Fault("the readings block is not parseable json: %s" % exc)


class Fault(object):
    """A document-level defect that stops the comparison: the block is absent, unfenced or unparseable."""

    def __init__(self, why):
        self.why = why

    def __repr__(self):
        return "Fault(%r)" % self.why


def compare(truth, claimed):
    """Every key is two-sided: a missing key is as much a defect as a wrong one."""
    if isinstance(claimed, Fault):
        return ["the readings could not be read: %s" % claimed.why]
    bad = []
    for k in sorted(set(truth) | set(claimed)):
        if k not in claimed:
            bad.append("%s: the document does not state it (computed %r)" % (k, truth[k]))
        elif k not in truth:
            bad.append("%s: the document states %r, which nothing computes" % (k, claimed[k]))
        else:
            a, b = truth[k], claimed[k]
            if isinstance(a, bool) or isinstance(b, bool) or a is None or b is None:
                if a is not b:
                    bad.append("%s: document %r, computed %r" % (k, b, a))
            elif isinstance(a, (int, float)) and isinstance(b, (int, float)):
                if abs(a - b) > max(1e-9, abs(a) * 1e-9):
                    bad.append("%s: document %r, computed %r" % (k, b, a))
            elif a != b:
                bad.append("%s: document %r, computed %r" % (k, b, a))
    return bad


def quote_check(doc_text, priors_path=PRIORS):
    """The prior text a row scores must be the REGISTERED text: every quoted clause must be in the extract."""
    priors = " ".join(io.open(priors_path, encoding="utf-8").read().split())
    quotes = re.findall(r'^>\s*(\S.*)$', doc_text, re.M)
    bad = []
    for q in quotes:
        q_norm = " ".join(q.split())
        if q_norm not in priors:
            bad.append("quoted clause not found in the registered priors: %r" % q_norm[:90])
    return quotes, bad


SHOWN = ("pb1_slope_at_b1", "pb1_bstar_mismatch", "pb1_bstar_substitution", "pb2_mismatch_at_b0.5_recomputed",
         "pb2_substitution_at_b1.0_recomputed", "pb3_b_floor_closed", "pb4_attack_success_same_R_check",
         "pb4_headline_harmful_readings")


# Numbers a document may state that are NOT readings of an instrument.  Each entry is a SHAPE plus the reason,
# and masking happens BEFORE the scan -- so a number is excused only while it keeps the shape that excuses it, and
# a shape that stops matching stops excusing anything (the list cannot rot into a blanket permission).
NON_READING_SHAPES = (
    (r"\b20\d\d-\d\d-\d\d\b", "a date (the registration's or this file's)"),
    (r"\b\d{4}\.\d{4,5}\b", "an arXiv id (a citation)"),
    (r"#\d+", "an issue reference"),
    (r"§\d+(?:\.\d+)*", "a section reference"),
    (r"\bTables? \d+", "a table reference"),
)


def stated_as(tok, value):
    """Does `value` compute the number the prose WROTE?  Checked at the token's own resolution.

    Prose rounds: a row may state `0.9667` for a computed `0.966667`.  Comparing at a fixed relative tolerance
    reported nine false failures the moment a row cited a rounded number -- the defect was in the check's
    resolution, not in the prose.  So the comparison is made at the resolution the number was STATED to:

      * a token with `d` DECIMALS accepts `round(value, d)`;
      * a token in SCIENTIFIC notation accepts `value` rounded to the token's number of SIGNIFICANT digits, since
        rounding a small number to 15 decimal places annihilates it (`round(2.22e-16, 15)` is `0.0`);
      * a token with none (an integer, i.e. a count) demands equality, because rounding a count would let `29`
        cover `29.6`.
    """
    m = re.match(r"[-−]?(\d+)(?:\.(\d+))?(?:[eE]([-−]?\d+))?$", tok)
    if not m:
        return False
    got = float(tok.replace("−", "-"))
    if m.group(3) is not None:
        sig = len((m.group(1) + (m.group(2) or "")).lstrip("0"))
        return got == float("%.*e" % (max(sig - 1, 0), value))
    d = len(m.group(2) or "")
    if d == 0:
        return got == value
    return got == round(value, d)


def numeric_vals(truth):
    """Every number the truth object computes, INCLUDING the elements of a quantity carried as a SET of readings.

    A quantity with several readings -- the cost-ratio ladder's `1/R` rate ratios are the one such quantity -- is a
    single object holding several numbers, and a scan that read only scalars could not see them: a number the
    instrument DID compute read as unbacked, so the row would have had to drop a real reading or declare it away
    with a non-reading shape.  The elements are flattened here, and a sequence element that is NOT a number is a
    REFUSAL rather than a silent skip -- silently skipping is exactly how a stated number becomes unbacked.
    """
    out = []
    for k, v in truth.items():
        stack = [v]
        while stack:
            x = stack.pop(0)
            if isinstance(x, bool) or x is None:
                continue
            if isinstance(x, (int, float)):
                out.append(float(x))
            elif isinstance(x, (list, tuple)):
                stack = list(x) + stack
            else:
                raise AssertionError(
                    "quantity %r carries a non-numeric %s (%r): a set of readings must hold numbers, and skipping "
                    "it is how a number the instrument computed becomes unbacked" % (k, type(x).__name__, x))
    return out


def prose_scan(doc_text, truth):
    """Every number in the PROSE must be a quantity the instruments compute, or a declared non-reading shape.

    Returns (number of tokens scanned, failures).  This is the two-sided half of the block check: the block proves
    the document states the computed values, and this proves the document states no OTHER value.  A number typed
    into the prose with no instrument behind it is exactly the failure the block cannot see, because the block is
    generated and the prose is not.
    """
    body = doc_text.split(BEGIN)[0]
    for pat, _ in NON_READING_SHAPES:
        body = re.sub(pat, " ", body)
    vals = numeric_vals(truth)
    # A sign and an exponent both belong to the token: `-0.012` is not `0.012`, and `2.2e-16` is not `16`.  The
    # sign class carries the Unicode MINUS SIGN as well as the ASCII hyphen, because the prose writes `−0.012` and
    # reading that as `+0.012` would compare a stated number against a different quantity.
    toks = sorted(set(re.findall(r"[-−]?\d+\.\d+(?:[eE][-−]?\d+)?|[-−]?\b\d+\b", body)))
    bad = []
    for tok in toks:
        if not any(stated_as(tok, x) for x in vals):
            bad.append("the prose states %s, which no quantity computes (at its own resolution) and no declared "
                       "non-reading shape excuses" % tok)
    return len(toks), bad


def report(doc_path=DOC, priors_path=PRIORS):
    missing = [p for p in list(RECORDS.values()) + [priors_path] if not os.path.exists(p)]
    if missing:
        print("NOT RUN -- missing input(s): %s" % ", ".join(missing))
        return 2
    truth = compute()
    txt, claimed = read_doc(doc_path)
    bad = compare(truth, claimed)
    quotes, qbad = quote_check(txt, priors_path)
    print("outcome check -- %d quantity(ies) computed from the instruments, %d quoted clause(s) checked"
          % (len(truth), len(quotes)))
    print("  records read: %s" % ", ".join("gate_%s_results.json" % k for k in sorted(RECORDS)))
    # The summary prints a few headline readings, and the names it prints are held to the truth: a printed key
    # that nothing computes would print `None` for a quantity this file HAS computed -- a report that reads as a
    # missing number when the number is present is a defect of the reading, so it exits non-zero.  (The first
    # version listed `..._at_b1_recomputed` / `..._at_b0.5_recomputed` while the truth builds those keys from
    # `%s` of a FLOAT, i.e. `..._at_b1.0_recomputed`; it printed `None` for a value it had just computed.)
    unbacked = [k for k in SHOWN if k not in truth]
    for k in SHOWN:
        if k in truth:
            print("  %-38s %s" % (k, truth[k]))
    bad += ["the report names %r, which no quantity computes" % k for k in unbacked]
    pshown, pbad = prose_scan(txt, truth)
    print("  prose scan:        %d number(s) in the prose, each a computed quantity or a declared non-reading "
          "shape" % pshown)
    bad += pbad
    if bad or qbad:
        for b in bad + qbad:
            print("OUTCOME CHECK: FAIL -- %s" % b)
        return 1
    print("OUTCOME CHECK: PASS -- the document states the computed values, and every quoted clause is the "
          "registered one")
    return 0


def selftest():
    """The battery: mutate the document, the prior extract and the records; each plant must move the exit code.

    The last case is the one this file exists for: a document whose numbers still agree with the instruments but
    whose QUOTE has been re-worded must fail, because a re-worded prior is not the prior that was registered.
    """
    cases, allok = [], True
    work = tempfile.mkdtemp(prefix="outcome-check-")
    try:
        for name, mutate, want, reach in [
            ("unmutated", lambda d: d, 0, _same),
            ("one quantity altered in the block (pb3_b_floor_closed)",
             lambda d: _repl(d, '"pb3_b_floor_closed": 0.126582', '"pb3_b_floor_closed": 0.13'), 1, _in_block),
            ("a quantity deleted from the block",
             lambda d: _repl(d, '"pb4_headline_harmful_readings": 20,', ""), 1, _in_block),
            ("a quantity invented in the block (no instrument computes it)",
             lambda d: _add_key(d, "pb1_fabricated", 1), 1, _in_block),
            # The case below is why the plant above had to be re-aimed: `END` sits AFTER the closing fence, so
            # the first version of the invented-key plant inserted text the checker never parses.  It is kept as
            # a case in its own right -- text outside the fence is not a reading, so it must NOT turn the check
            # red -- and `_outside_block` asserts the plant really did land outside.
            ("a key appended after the closing fence (not a reading, so not caught)",
             lambda d: _repl(d, END, '"pb1_after_fence": 1,\n' + END), 0, _outside_block),
            ("the readings block holds unparseable json",
             lambda d: _repl(d, '```json\n{\n', '```json\n{ "pb1_slope_at_b1": ,\n'), 1, _faults),
            ("the json fence removed from the block",
             lambda d: _repl(d, '```json\n', ''), 1, _faults),
            ("a quoted prior clause re-worded",
             lambda d: _repl(d, "the gate's expected harm is non-increasing in escalation coverage",
                             "the gate's expected loss is non-increasing in escalation coverage"), 1, None),
            ("a number invented in the prose (the block is untouched)",
             lambda d: _repl(d, "0.08675 of the no-gate loss", "0.08676 of the no-gate loss"), 1, _prose_only),
            ("a positive reading written where its sign belongs",
             lambda d: _repl(d, "the slope is −0.012", "the slope is 0.012"), 1, _prose_only),
        ]:
            dst = os.path.join(work, "outcomes_%d.md" % len(cases))
            before = io.open(DOC, encoding="utf-8").read()
            txt = mutate(before)
            if reach:
                reach(before, txt)          # each predicate asserts its own "the plant landed" property
            else:
                assert txt != before, "plant %r changed nothing (inert)" % name
            io.open(dst, "w", encoding="utf-8").write(txt)
            rc = report(dst, PRIORS)
            ok = rc == want
            allok = allok and ok
            cases.append((name, want, rc, ok))
        # A defect of the REPORT itself, not of any document: the summary's key list names a quantity nothing
        # computes.  No document mutation can reach it, so the battery mutates the module instead.
        global SHOWN
        keep, SHOWN = SHOWN, SHOWN + ("pb1_never_computed",)
        try:
            rc = report(dst, PRIORS)
        finally:
            SHOWN = keep
        ok = rc == 1
        allok = allok and ok
        cases.append(("the report's own key list names a quantity nothing computes", 1, rc, ok))

        # The declared non-reading shapes are excuses, so they get controls of their own -- two-sided: each shape
        # must excuse the text it names, and must NOT excuse a near miss that no longer has the shape.
        truth = compute()
        for name, text, want_bad in [
            ("shape control: a date, an arXiv id and an issue ref are excused",
             "registered 2026-09-21 (issue #93) citing 2609.11596\n", 0),
            ("shape control: an id with six digits after the dot is NOT excused",
             "citing 2609.115961\n", 1),
            ("shape control: a bare integer with no shape around it is NOT excused",
             "the count read 487\n", 1),
        ]:
            rc = 1 if prose_scan(text, truth)[1] else 0
            ok = rc == want_bad
            allok = allok and ok
            cases.append((name, want_bad, rc, ok))

        # The scan compares a stated number at the resolution it is STATED to, so that rule owes its own cases:
        # rounding must be accepted where the prose rounds, and a wrong number at the same resolution refused.
        # (A fixed tolerance reported nine false failures the moment a row cited a rounded number -- the control
        # that would have caught it is these six lines.)
        for name, text, want_bad in [
            ("resolution: a rounded decimal is accepted at its own resolution",
             "coverage was 0.966667 and reads 0.9667\n", 0),
            ("resolution: a wrong decimal at the same resolution is refused",
             "coverage was 0.966667 and reads 0.9673\n", 1),
            ("resolution: a count is exact, so its value is accepted",
             "the estimator covered 29 in-axis readings\n",
             0),
            ("resolution: the same count off by one is refused",
             "the estimator covered 31 in-axis readings\n", 1),
            ("resolution: a scientific-notation token is checked at its significant digits",
             "curvature 2.220446049250313e-16\n", 0),
            ("resolution: a scientific-notation digit off is refused",
             "curvature 2.220446049250314e-16\n", 1),
        ]:
            rc = 1 if prose_scan(text, truth)[1] else 0
            ok = rc == want_bad
            allok = allok and ok
            cases.append((name, want_bad, rc, ok))

        # A quantity carried as a SET of readings owes the same cases: its elements must be readable to the scan
        # (otherwise the row is forced to drop a number the instrument computed), a number no set holds must still
        # be refused, and an element that is not a number must be a REFUSAL rather than a silent skip.
        for name, text, want_bad in [
            ("a set quantity: an element of the cost-ratio ladder's rate ratios is accepted",
             "the consecutive differences fall by 10.0000 each decade\n", 0),
            ("a set quantity: a number no element of any set holds is still refused",
             "the consecutive differences fall by 10.1250 each decade\n", 1),
        ]:
            rc = 1 if prose_scan(text, truth)[1] else 0
            ok = rc == want_bad
            allok = allok and ok
            cases.append((name, want_bad, rc, ok))
        for name, bad_truth, want_raise in [
            ("a set quantity whose element is not a number is a REFUSAL, not a silent skip",
             {"q": ["0.5", 1.0]}, True),
            ("a set quantity whose elements are all numbers is read, not refused",
             {"q": [10.0, 9.99]}, False),
        ]:
            try:
                numeric_vals(bad_truth)
                raised = False
            except AssertionError:
                raised = True
            ok = raised == want_raise
            allok = allok and ok
            cases.append((name, int(want_raise), int(raised), ok))
    finally:
        shutil.rmtree(work, ignore_errors=True)
    print("OUTCOME CHECK BATTERY -- %d case(s), %d caught" % (len(cases), sum(1 for c in cases if c[3])))
    for name, want, got, ok in cases:
        print("  %-6s %-72s exit %d (want %d)" % ("ok" if ok else "MISSED", name, got, want))
    print("SELFTEST: %s" % ("PASS" if allok else "FAIL"))
    return 0 if allok else 1


def _repl(text, old, new):
    assert old in text, "plant anchor absent: %r" % old
    out = text.replace(old, new, 1)
    assert out != text, "plant changed nothing (inert): %r" % old
    return out


def _add_key(text, key, val):
    """Add a key to the readings block BY WAY OF THE PARSE -- so the plant cannot land outside the fence."""
    m = re.search(r'```json\n(.*?)\n```', text, re.S)
    assert m, "no json fence to mutate"
    obj = json.loads(m.group(1))
    obj[key] = val
    new = "```json\n" + json.dumps(obj, indent=1, sort_keys=True) + "\n```"
    out = text[:m.start()] + new + text[m.end():]
    assert out != text, "plant changed nothing (inert)"
    return out


def _same(before, after):
    """The control case: the document is handed over unmutated, so it must NOT change."""
    assert before == after, "the unmutated control was mutated"
    return True


def _in_block(before, after):
    """The plant reached the checker's parse: the block still parses, and it changed."""
    b, a = read_text(before)[1], read_text(after)[1]
    assert not isinstance(a, Fault), "the plant broke the block instead of reaching the parse: %s" % a.why
    assert a != b, "the plant did not change the parsed block"
    return True


def _outside_block(before, after):
    a = read_text(after)[1]
    assert not isinstance(a, Fault), "the plant broke the block"
    assert a == read_text(before)[1], "the plant DID reach the parse; it is not an outside-the-fence plant"
    return True


def _faults(before, after):
    """The plant's intended reach IS the Fault: the block became unreadable."""
    a = read_text(after)[1]
    assert isinstance(a, Fault), "the plant was expected to break the block, but it still parses"
    return True


def _prose_only(before, after):
    """The plant reached the PROSE scan: the block reads identically, and only the text around it changed."""
    assert read_text(after)[1] == read_text(before)[1], "the plant moved the readings block; it is not a prose plant"
    assert after != before, "the plant changed nothing"
    return True


def main(argv):
    if "--selftest" in argv:
        return selftest()
    if "--emit" in argv:
        print(block(compute()))
        return 0
    if "--write-doc" in argv:
        txt = io.open(DOC, encoding="utf-8").read()
        pre, rest = txt.split(BEGIN, 1)
        _, post = rest.split(END, 1)
        io.open(DOC, "w", encoding="utf-8").write(pre + block(compute()) + post)
        print("wrote the computed readings block into %s" % DOC)
        return 0
    return report()


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
