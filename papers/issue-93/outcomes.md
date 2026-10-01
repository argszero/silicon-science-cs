# #93 — the per-prior `Outcome` rows

Registered 2026-09-21 (issue #93, `in-preparation`). This file is the working source of the `Outcome` section the
registration promises to write at submission: for each registered prior, whether the results **confirm** it,
**contradict** it, or leave it **unresolved**, with the reading each verdict rests on.

**How the rows are held to their evidence.** `outcome_check.py` owns every number stated here: it recomputes
each one from the instruments (imported, never copied) or reads it from an instrument's committed record, and
fails on any disagreement between this document and that computation. The readings block at the bottom is
**generated** by that file (`--write-doc`), never typed beside it. The check is **two-sided**: besides the block,
it scans the prose and requires every number there to be a quantity the instruments compute (the only exceptions
are declared by shape — a date, an arXiv id, an issue number, a section or table reference), so a figure typed
into the prose with nothing behind it fails as loudly as a block value that disagrees. `--selftest` runs the
battery, in which every case is a plant proved to reach the reading it targets and to move the exit code; the
battery prints its own count when it runs.

**Which text a row scores.** The registered wording only — quoted verbatim from `registration_priors.md`, a
stored extract of issue #93's body — because a prior is scored as registered, not as remembered. Where a
registered sentence reads two ways, **both readings are scored and both are reported**, and the wording defect is
recorded as a finding about the registration rather than silently resolved.

| prior | read by | verdict |
|---|---|---|
| PB1 monotone safety | v0 (`b = 1` closure), v1 (the map, slope sign law) | **refuted below the slope threshold; confirmed at the boundary `b = 1`** — the registered direction |
| PB2 the accuracy axis is the binding one | v4 (the registration's own metric (b)), v1 (sign law) | **refuted in its "every fidelity" clause; confirmed at `b = 1`** for a misrepresenting channel, refuted at every registered fidelity for a laundering one |
| PB3 escalation is monotone ("escalate more") | v1 (affineness + sign law + the fatigue arm) | **refuted structurally as registered; the registered shape appears only under a mechanism the registration never names** |
| PB4 a use-time check closes the channel | v2 (the design ladder), v3 (headline + external arm) | **the published prediction is refuted and the registered opposite direction is confirmed** |

## PB1 — monotone safety (the model the deployed field implies)

Registered claim:

> the gate's expected harm is non-increasing in escalation coverage `s` and non-decreasing in reviewer accuracy `a`, at every fidelity `b` — i.e. adding or strengthening a human gate never increases expected harm.

> **The study is designed to locate the region where this prediction fails, and the registered direction is that it fails for `b < 1` through the laundering channel (an approval of a benign rendering authorizes a harmful execution) and holds on the boundary `b = 1`.**

**Read by** v0 (the screening closure at `b = 1`) and v1 (the map at `b < 1`, the slope sign law and the sign
thresholds).

**The coverage clause.** The value is affine in coverage at every point of the map (worst relative second
difference 2.220446049250313e-16 over 81 cells), so the clause reduces to the sign of the coverage slope, and the
slope is affine in fidelity as well. Two channels, two different thresholds, and the difference between them is
the paper's mechanism:

* a **misrepresenting** channel adds nothing at zero coverage, so its value at full coverage *is* its slope: the
  sign changes at the slope threshold 0.08, and there the slope is −0.012 — escalation strictly increases harm;
* a **laundering** channel is already net-harmful with coverage switched off (harmful at zero coverage for every
  fidelity below 1, and exactly zero at the boundary), so it has **two** thresholds: its slope turns positive at
  0.126582, while its gate value only crosses zero at 0.8559. Between them the gate loses whatever the coverage
  decision does.

At the boundary the prior names, the slope is +0.138 (the screening case). So the coverage clause is **refuted
below each channel's own slope threshold and confirmed above it**, which is exactly the registered direction:
the prediction fails for `b < 1` and holds on the boundary `b = 1`.

**The accuracy clause, and a wording defect in the registration.** The sentence's second clause is stated in the
direction *opposite* to its own gloss ("never increases expected harm") and to its justification (the
screening-channel argument, under which a more accurate reviewer blocks more harm). Both readings were scored
rather than one being chosen:

* **as written** ("non-decreasing in `a`"): at the boundary the harm *falls* in accuracy (slope −0.2), so the
  literal clause is refuted exactly where the gate is a screening channel — and it holds at zero fidelity only
  because the accuracy axis is then **exactly inert** (the derivative is a zero, not a small number).
* **as glossed** ("non-increasing in `a`"): it holds at `b = 1` and holds weakly at `b = 0`.

The literal clause is therefore **refuted at the boundary and trivially satisfied where the axis is dead** — the
opposite pattern to the prior's own spirit. Recorded as a finding about the registration's wording (its two
clauses are correct in opposite directions), not as a result about the model.

**Verdict.** The registered *direction* is **confirmed**: the prediction fails for `b < 1` through the
laundering channel and holds on the boundary. The registered *sentence* carries a clause whose literal direction
contradicts its gloss; both readings are reported above.

## PB2 — the accuracy axis is the binding one

Registered claim:

> the marginal reduction in expected harm from one unit of reviewer accuracy at fixed coverage exceeds the marginal reduction from the same unit of binding fidelity, at every fidelity level — i.e. reviewer quality is the axis that pays.

Its registered justification names the opposite direction as what the harness exists to measure, and the
registration's own success metric (b) is this ratio at the three registered fidelities.

**Read by** v4, which was built for exactly this quantity (the registration's metric (b), read from the exact
enumeration with the closed form as the prediction), cross-checked here by recomputation at every cell.

**Readings.** The ratio of the accuracy derivative to the fidelity derivative, at the registered fidelities:

* misrepresenting channel: 0 (at `b = 0`, where the axis is inert), 0.666667 (at `b = 0.5`), 1.333333 (at `b = 1`);
* laundering channel: 0, 0.104384, 0.208768.

The record and the recomputation agree at all six cells. Above 1 the accuracy axis pays more than the binding
axis; below 1 it pays less. So PB2's universal clause **fails at `b = 0.5`** for a misrepresenting channel and at
**every** registered fidelity for a laundering one, and holds only at `b = 1`. The registered opposite direction
("fidelity pays more, and the gap widens as `b` falls") is confirmed.

**The boundary between the two regimes is the reviewer's own margin.** The ratio reaches 1 at 0.75 = `a − f`, the
reviewer's Youden index (numeric 0.75 against the predicted 0.75, deviation 2.986499936241671e-13) for a
misrepresenting channel, and **nowhere** on the axis for a laundering one, whose predicted crossing 4.79 lies
outside it — reported by the instrument as a refusal (no crossover exists) rather than as a missing number.

**Verdict.** **Refuted in its "every fidelity level" clause** (0.666667 at the registered `b = 0.5`; never above
1 for laundering), **confirmed at `b = 1`**. The registered opposite direction is confirmed, with the crossover
now located: accuracy pays more than binding exactly when fidelity exceeds the reviewer's discriminating margin.

## PB3 — escalation is monotone in the "escalate everything" direction

Registered claim:

> the optimal coverage is `s* = 1` (escalate every action) whenever the harm-to-interruption ratio `L/c` is large, so the practical rule is "escalate more".

> the optimum is interior and `s*` is non-increasing in `b`, reaching the floor (never escalate) below `b*` when laundering dominates.

**Read by** v1 (the map in closed form: affineness, the sign law, and the fatigue arm).

**The value is affine in coverage at every point of the map** (worst relative second difference
2.220446049250313e-16 over 81 cells), so **no interior optimum exists in this model, at any fidelity** — the
registered "the optimum is interior" is **refuted structurally**, not merely at the boundary. The mechanical
reason: the reviewer's rejection probability is conditioned on escalation, so every state's probability is linear
in `s` and no curvature can appear.

**The literal clause** ("escalate more"): at `b = 1` the slope is +0.138, so `s* = 1` — the rule holds there. But
the same `L/c` gives `s* = 0` below each channel's slope threshold (0.08 misrepresenting, 0.126582 laundering), so
the practical rule is not a property of `L/c` alone: it is gated by fidelity, which the prior does not mention.

**The registered direction appears only under a mechanism the registration never names.** With a linear fatigue
coupling (the reviewer's sensitivity degrading with escalation volume), the vertex is interior for every fidelity
above the floor 0.126582 and sits at the floor below it: 7 cells above the floor are interior, 3 below it are
corners, the grid argmax matches the closed-form vertex to 0.00208333333333334 (grid step 0.005), and the floor
**equals the laundering channel's own `eta = 0` sign-law threshold** — the floor is the sign law's number. So
PB3's shape is a property of **fatigue**, not of approval gates; naming the mechanism is what makes the registered
shape appear.

**Verdict.** The literal clause is **confirmed at `b = 1` and refuted below the slope thresholds**; the registered
"interior optimum, non-increasing in `b`, reaching the floor" is **confirmed conditional on a fatigue coupling the
registration does not name, and refuted structurally without it**.

## PB4 — re-checking at execution time closes the channel

Registered claim (the published position):

> adding a use-time check of the approved object (the EBL-Core shape, 2609.11596) removes the laundering channel even when the rendering itself is unfaithful, because the check is independent of the rendering.

> the repair is **fidelity-equivalent, not independent** — a use-time check that reads the same derived representation as the rendering restores `b` only up to the faithfulness of that representation, so its marginal value is itself a function of `b`, and this is a measurable, and possibly refuting, claim about a proposed repair.

**Read by** v2 (the design ladder: six designs over the same channel, each class of defect read separately) and
v3 (the headline's sensitivity and the external-validation arm).

**The published prediction fails twice, and the two failures are the same kind of object — the representation:**

* a check that reads the same representation the reviewer read **cannot see the invisible substitution class**:
  attack success 0.3333 survives it, against 0 for the only design that re-derives the request at use time;
* it **cannot see the display class** either: without the canonical rendering the check leaves 0.045 of value on
  the table at the defaults, i.e. 0.15 per unit of display defect.

**The registered direction is confirmed in its measurable form.** The check's value is exactly the class it can
read (1 per unit of visible substitution), its blind spot is exactly the class it cannot (1 per unit of invisible
substitution), and the two repairs are **complements, not substitutes**: the canonical rendering is worth
0.04500000000000001 at the defaults, and the design with a re-derived use-time check is the only one whose
residual channel is empty (0 surviving classes).

**The unpublished part of the claim is where the external anchor reproduces.** The published "0 % attack success
when binding holds" is reproduced exactly where its own claim lives — a fully representation-visible channel gives
0 at both the same-representation and the re-derived check — and degrades exactly as the channel becomes
invisible (0.25 at one-tenth invisible, 0.5 at half). The ladder's ordering and the published ordering are both
reproduced (the re-derived arm beats the text-approval arm; the unbound arm is worst at 1.0, inside the published
0.68–1.00 band), and two designs are worth **less than no gate at all**.

**Verdict.** **The published prediction is refuted and the registered opposite direction is confirmed**: the
repair is not independent of the rendering; its marginal value is a function of the faithfulness of the
representation it reads, and the two published repairs are complements.

## What this leaves for the registration's success-metric list

| metric | status |
|---|---|
| (a) the boundary `b*(a, s, L, c)` with bootstrap CIs, **and its dependence on `L/c`** | **fully read** — (i) **the point** (v1): exact and bisection-verified; (ii) **the interval** (v5): the estimator recovers the exact boundary (worst error 0.0538 against a worst width 0.154), coverage over the 30 in-axis readings 29/30 = 0.9667 with Wilson [0.8333, 0.9941] (the nominal inside), the set being the fidelities where the measured value is not distinguishable from zero, its width the value's noise over its fidelity slope (worst departure 0.079 in the regime the law derives) and a **measured** `1/√n` law (1.981, 2.042 at four times the sample); at the defaults the misrepresentation boundary is [0.0528, 0.1526] against a laundering boundary of [0.8491, 0.8591] — the same sample locates the laundering boundary an order of magnitude more precisely; (iii) **the cost-ratio dependence** (v6): the two channels differ in kind — the misrepresentation bar is a `1/R` hyperbola, **zero at `L/c = 110`** and negative beyond, so it exists only on the bounded window `(6.875, 110)`, while the laundering bar **saturates at 0.8333 and never vanishes** and exists on `(0.104, ∞)`; the two bars cross exactly where **both sit at the top of the axis**, at `R = (1 + (cb/c)(1−π)f)/(πa) = 6.875` (the bisection agrees to 8.9e-16), so below it **no fidelity buys the gate**, above it the laundering channel sets the binding threshold; the limits are approached at the measured `1/R` rate — the misrepresentation ladder's consecutive difference ratios 10.0000 and 10.0000, the laundering ladder's 10.0094 and 10.0009; and the interval comparison is reproduced at two further cost ratios (4 of 4 covered). **Two wording findings are recorded.** First, "with bootstrap CIs" names no carrier, and the only reading this study can implement is estimator uncertainty — a CI over `(a, s, L, c)` themselves is not implementable, since they are design points with ground truth by construction. Second, the clause "its dependence on `L/c`" reads as if `L/c` were the only ratio that matters: the registered symbol `b*(a, s, L, c)` **omits the false-block cost `cb` and the laundering factor `η`**, both of which the model's own algebra carries and both of which a control shows moving the boundary (varying `cb/c` moves **both** boundaries; varying `η` moves only the laundering one, exactly; varying the coverage `s` likewise moves only the laundering one). The 12 readings whose exact crossing lies outside the axis are excluded by a declared rule and published with their endpoint values, and the 21 `none`-channel readings have no boundary to cover at all. |
| (b) the axis-sensitivity ratio at `b in {0, 0.5, 1}` | **read** (v4) — this is PB2's own metric, reported above. |
| (c) the interior escalation optimum `s*` and whether it falls to the floor | **read** (v1) — under a named fatigue coupling; structurally absent without one. |
| (d) the marginal value of use-time checking as a function of the representation's faithfulness | **read** (v2) — the per-class decomposition. |
| (e) external validation: the published orderings and the anchor's measured values | **read** (v2, v3) — both orderings reproduced, the anchor's 0 % reproduced exactly and its measured low-fidelity end landing where the law says the gate is net-harmful. |

The headline's own sensitivity is read too: 20 of 35 (cell, design) readings are net-harmful gates, in all 7 of
the parameter grid's cells and across all 5 gated designs, with the weakest instance 0.08675 of the no-gate loss
on the wrong side of zero — so the headline is not one construction's artefact.

<!-- readings:begin -->
```json
{
 "a_defaults_mismatch_exact": 0.08,
 "a_defaults_mismatch_hi": 0.1526,
 "a_defaults_mismatch_lo": 0.0528,
 "a_defaults_mismatch_width": 0.0998,
 "a_defaults_substitution_exact": 0.8559,
 "a_defaults_substitution_hi": 0.8591,
 "a_defaults_substitution_lo": 0.8491,
 "a_defaults_substitution_width": 0.01,
 "a_estimator_worst_dev": 0.05378,
 "a_estimator_worst_width": 0.154022,
 "a_interval_covered_fieller": 29,
 "a_interval_denominator": 30,
 "a_interval_excluded_out_of_axis": 12,
 "a_interval_no_target": 21,
 "a_interval_nominal": 0.95,
 "a_interval_rate_bootstrap": 0.933333,
 "a_interval_rate_fieller": 0.966667,
 "a_interval_wilson_hi": 0.9941,
 "a_interval_wilson_lo": 0.8333,
 "a_mapping_worst_se": 2.177,
 "a_null_denominator": 21,
 "a_null_rate": 0.047619,
 "a_null_rejections": 1,
 "a_rc_R_zero_mismatch": 110.0,
 "a_rc_Rc": 6.875,
 "a_rc_Rc_closed_vs_bisected": 8.881784197001252e-16,
 "a_rc_bar_at_Rc_mismatch": 1.0,
 "a_rc_bar_at_Rc_substitution": 1.0,
 "a_rc_eta_moves_mismatch": 0.0,
 "a_rc_eta_moves_substitution": 0.103262,
 "a_rc_interval_covered": 4,
 "a_rc_interval_n": 4,
 "a_rc_limit_mismatch": -0.066667,
 "a_rc_limit_substitution": 0.833333,
 "a_rc_rate_ratios": [
  10.0,
  10.0
 ],
 "a_rc_rate_ratios_substitution": [
  10.0094,
  10.0009
 ],
 "a_rc_s_moves_mismatch": 0.0,
 "a_rc_s_moves_substitution": 0.102954,
 "a_rc_second_route_worst": 3.3306690738754696e-16,
 "a_rc_sweep_checked": 12,
 "a_rc_sweep_readings": 24,
 "a_rc_sweep_skipped": 12,
 "a_rc_t_moves_mismatch": 0.013333,
 "a_rc_window_substitution": 0.1042,
 "a_scaling_ratio_mismatch": 1.9811,
 "a_scaling_ratio_substitution": 2.0424,
 "a_scaling_worst_dev": 0.042351,
 "a_states_bounded": 43,
 "a_states_flat": 20,
 "a_width_law_regime": 4.3826,
 "a_width_law_worst_dev_in_regime": 0.07903,
 "external_coverage_n": 315,
 "external_coverage_rate": 0.971429,
 "external_vac_beats_text": true,
 "pb1_bstar_mismatch": 0.08,
 "pb1_bstar_substitution": 0.8559,
 "pb1_curvature_cells": 81,
 "pb1_curvature_worst_relative": 2.220446049250313e-16,
 "pb1_dEda_at_b0": 0.0,
 "pb1_dEda_at_b1": -0.2,
 "pb1_laundering_has_two_thresholds": true,
 "pb1_slope_at_b1": 0.138,
 "pb1_slope_mismatch_at_b0": -0.012,
 "pb1_slope_sign_follows_its_own_threshold": true,
 "pb1_slope_threshold_mismatch": 0.08,
 "pb1_slope_threshold_substitution": 0.126582,
 "pb1_substitution_harmful_at_zero_coverage_below_1": true,
 "pb1_value_threshold_substitution": 0.8559,
 "pb2_accuracy_pays_more_at_b05_mismatch": false,
 "pb2_accuracy_pays_more_at_b1_mismatch": true,
 "pb2_crossover_deviation": 2.986499936241671e-13,
 "pb2_crossover_predicted_laundering": 4.79,
 "pb2_crossover_stated": 0.75,
 "pb2_mismatch_at_b0.0_recomputed": -0.0,
 "pb2_mismatch_at_b0.0_record": 0.0,
 "pb2_mismatch_at_b0.5_recomputed": 0.666667,
 "pb2_mismatch_at_b0.5_record": 0.666667,
 "pb2_mismatch_at_b1.0_recomputed": 1.333333,
 "pb2_mismatch_at_b1.0_record": 1.333333,
 "pb2_registered_b_high": 1.0,
 "pb2_registered_b_low": 0.0,
 "pb2_registered_b_mid": 0.5,
 "pb2_substitution_at_b0.0_recomputed": -0.0,
 "pb2_substitution_at_b0.0_record": 0.0,
 "pb2_substitution_at_b0.5_recomputed": 0.104384,
 "pb2_substitution_at_b0.5_record": 0.104384,
 "pb2_substitution_at_b1.0_recomputed": 0.208768,
 "pb2_substitution_at_b1.0_record": 0.208768,
 "pb3_affine_worst_relative": 2.220446049250313e-16,
 "pb3_all_corners": true,
 "pb3_b_floor_closed": 0.126582,
 "pb3_fatigue_cells_above": 7,
 "pb3_fatigue_cells_below": 3,
 "pb3_fatigue_grid_step": 0.005,
 "pb3_fatigue_interior_above_floor": true,
 "pb3_floor_equals_sign_law_eta0": true,
 "pb3_grid_vs_closed": 0.00208333333333334,
 "pb4_anchor_degradation_10pct": 0.25,
 "pb4_anchor_degradation_50pct": 0.5,
 "pb4_anchor_degradation_matches_sigma_share": true,
 "pb4_anchor_published_zero_reproduced": true,
 "pb4_attack_success_rederived_check": 0.0,
 "pb4_attack_success_same_R_check": 0.3333,
 "pb4_attack_success_unbound": 1.0,
 "pb4_blind_spot_per_unit_sigma_i": 1.0,
 "pb4_check_value_per_unit_sigma_v": 1.0,
 "pb4_d4_residual_classes": 0,
 "pb4_designs_below_no_gate": 2,
 "pb4_display_residual_at_delta_030": 0.04500000000000001,
 "pb4_display_residual_per_unit_delta": 0.15,
 "pb4_headline_cells": 7,
 "pb4_headline_designs": 5,
 "pb4_headline_harmful_readings": 20,
 "pb4_headline_min_margin": 0.08675,
 "pb4_headline_readings": 35,
 "pb4_published_band_contains_unbound": true,
 "pb4_published_band_high": 1.0,
 "pb4_published_band_low": 0.68
}
```
<!-- readings:end -->
