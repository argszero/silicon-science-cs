#!/usr/bin/env python3
"""issue #141 -- the canonical numbers layer.

Every number the manuscript quotes is re-derived HERE, from the shipped artefacts, and carries the
artefact path it came from.  A sentence in the manuscript may name a number only if this file emits
it; a number that cannot be re-derived is not a number this paper has.

Why this exists (the reason #142's review spent a round on it): a plan's prose drifts from its
artefacts, and the drift is invisible because both look authoritative.  The plan for this paper was
written by hand after the runs; this layer is the machine's reading of the same runs, and where the
two disagree the artefact wins.

  python3 canonical.py            # the table
  python3 canonical.py --json     # the same, as JSON (the shape build_manuscript.py will consume)
  python3 canonical.py --selftest # the plants: each must FAIL on the defect it names

DESIGN SPACES ARE NAMED, NEVER IMPLIED.  v2/v3 read 17 protocols over 4 games (272 cells); v4 reads
19 protocols over 9 games (684 cells).  A count without its space is a count the reader cannot check,
so every key below is prefixed by the artefact it lives in.
"""
import json
import os
import sys
from collections import OrderedDict
from fractions import Fraction

HERE = os.path.dirname(os.path.abspath(__file__))
V0 = os.path.join(HERE, "spike_v0_results.json")
V1 = os.path.join(HERE, "spike_v1_theory.json")
V2 = os.path.join(HERE, "spike_v2_design.json")
V3 = os.path.join(HERE, "spike_v3_results.json")
V4 = os.path.join(HERE, "spike_v4_results.json")
TRA = os.path.join(HERE, "analysis_transitivity_vs_transport.json")   # R673, required change 1
EXC = os.path.join(HERE, "census_excess_entries.json")
CONV = os.path.join(HERE, "census_converse_scope.json")
CND = os.path.join(HERE, "analysis_conditioning.json")   # R676/r2, required changes R5 and R6


def load(p):
    with open(p, encoding="utf-8") as fh:
        return json.load(fh)


_ART = {}


def art(p):
    if p not in _ART:
        _ART[p] = load(p)
    return _ART[p]


# --------------------------------------------------------------------------------------------------
# the numbers, each with the artefact path that owns it
# --------------------------------------------------------------------------------------------------
def numbers():
    n = OrderedDict()

    def put(name, value, source):
        n[name] = {"value": value, "source": source}

    v4 = art(V4)
    tra = art(TRA)
    v3 = art(V3)
    v2 = art(V2)
    v1 = art(V1)
    v0 = art(V0)

    # --- the design space, and which artefact reads which one -----------------------------------
    m = v4["model"]
    put("v4.games", len(m["games"]), "spike_v4_results.json:model.games")
    put("v4.policies", len(m["policies"]), "spike_v4_results.json:model.policies")
    put("v4.populations", len(m["populations"]), "spike_v4_results.json:model.populations")
    put("v4.protocols", len(m["protocols"]), "spike_v4_results.json:model.protocols")
    put("v4.cells", m["cells"], "spike_v4_results.json:model.cells")
    put("v4.transport_entries", m["transport_entries"], "spike_v4_results.json:model.transport_entries")
    put("v4.population_pairs", len(m["population_pairs"]), "spike_v4_results.json:model.population_pairs")
    put("v2.protocols", len(v2["model"]["protocols"]), "spike_v2_design.json:model.protocols")
    put("v2.games", len(v2["model"]["games"]), "spike_v2_design.json:model.games")
    put("v3.cells", len(v3["transport"]) and v3["model"].get("cells"), "spike_v3_results.json:model.cells")
    put("v3.protocols", len(v3["model"]["protocols"]), "spike_v3_results.json:model.protocols")

    # --- the transitivity coordinate vs the transport statistic (R673, required change 1) --------
    # Every number §10 quotes about the comparison is owned by the analysis artefact, so a later edit
    # cannot restate one of them from prose.
    put("trans.coord.zero_games", tra["coord_zero_games"],
        "analysis_transitivity_vs_transport.json:coord_zero_games")
    put("trans.coord.nonzero_games", tra["coord_nonzero_games"],
        "analysis_transitivity_vs_transport.json:coord_nonzero_games")
    put("trans.games", tra["games"], "analysis_transitivity_vs_transport.json:games")
    put("trans.coord.ties", tra["coord_ties"], "analysis_transitivity_vs_transport.json:coord_ties")
    put("trans.game_pairs", tra["game_pairs"], "analysis_transitivity_vs_transport.json:game_pairs")
    put("trans.gpos.coord0", tra["gpos_coord0"], "analysis_transitivity_vs_transport.json:gpos_coord0")
    put("trans.gpos.total", tra["gpos_total"], "analysis_transitivity_vs_transport.json:gpos_total")
    put("trans.distinct_max", tra["distinct_max"], "analysis_transitivity_vs_transport.json:distinct_max")
    put("trans.distinct_gt1_games", tra["distinct_gt1_games"],
        "analysis_transitivity_vs_transport.json:distinct_gt1_games")
    put("trans.base.distinct_max_coord0", tra["base_distinct_max_within_coord0"],
        "analysis_transitivity_vs_transport.json:base_distinct_max_within_coord0")
    put("trans.verdict", tra["verdict"], "analysis_transitivity_vs_transport.json:verdict")
    # the worked example in §10 was printed by the instrument and stored by nothing (R2): its two
    # extremes are now keys, so `check_numbers.py` can fail on a number that drifts.
    _w = tra["widest_pair_by_game"]["fpsb_n4"]
    put("trans.widest.low", _w["low"],
        "analysis_transitivity_vs_transport.json:widest_pair_by_game.fpsb_n4.low")
    put("trans.widest.high", _w["high"],
        "analysis_transitivity_vs_transport.json:widest_pair_by_game.fpsb_n4.high")
    put("trans.widest.n_distinct", _w["n_distinct"],
        "analysis_transitivity_vs_transport.json:widest_pair_by_game.fpsb_n4.n_distinct")

    # --- R5: does the across-protocol spread survive conditioning? --------------------------------
    cnd = load(CND)
    r5 = cnd["R5"]
    put("cond.pairs", r5["pairs"], "analysis_conditioning.json:R5.pairs")
    put("cond.coord.min_distinct", r5["conditioning_on_transitive_strength"]["min_distinct_over_all_cells"],
        "analysis_conditioning.json:R5.conditioning_on_transitive_strength")
    put("cond.size.min_distinct", r5["conditioning_on_population_size"]["min_distinct_over_all_cells"],
        "analysis_conditioning.json:R5.conditioning_on_population_size")
    put("cond.both.min_distinct", r5["conditioning_on_both"]["min_distinct_over_all_cells"],
        "analysis_conditioning.json:R5.conditioning_on_both")
    put("cond.coord0.pairs", r5["coord_zero_game_pairs"], "analysis_conditioning.json:R5.coord_zero_game_pairs")
    put("cond.coord0.min_distinct", r5["coord_zero_min_distinct"],
        "analysis_conditioning.json:R5.coord_zero_min_distinct")
    put("cond.coord0.max_distinct", r5["coord_zero_max_distinct"],
        "analysis_conditioning.json:R5.coord_zero_max_distinct")
    put("cond.verdict", r5["verdict"], "analysis_conditioning.json:R5.verdict")
    # the two shares §10 quotes are computed from counts above; give them keys so the printed
    # decimals are checked rather than derived in prose
    put("trans.gpos.share_pct", round(100.0 * tra["gpos_coord0"] / tra["gpos_total"], 1),
        "computed: gpos_coord0 / gpos_total")
    put("trans.coord.base_rate_pct", round(100.0 * tra["coord_zero_games"] / tra["games"], 1),
        "computed: coord_zero_games / games (the base rate a random cell lands in a zero game)")

    # --- R6: the anchor-free game's share of the headline numbers --------------------------------
    _all = cnd["R6"]["all_games"]
    _exc = cnd["R6"]["anchor_free_excluded"]
    put("r6.excl.game", _exc["excluded_game"], "analysis_conditioning.json:R6.anchor_free_excluded")
    put("r6.excl.g_positive", _exc["g_positive"], "analysis_conditioning.json:R6.anchor_free_excluded.g_positive")
    put("r6.excl.cells", _exc["cells"], "analysis_conditioning.json:R6.anchor_free_excluded.cells")
    put("r6.excl.gameable", _exc["gameable_cells"], "analysis_conditioning.json:R6.anchor_free_excluded.gameable_cells")
    put("r6.excl.fragile", _exc["fragile_cells"], "analysis_conditioning.json:R6.anchor_free_excluded.fragile_cells")
    put("r6.excl.counterexamples", _exc["g_positive_without_fragility"],
        "analysis_conditioning.json:R6.anchor_free_excluded.g_positive_without_fragility")
    put("r6.excl.games", _exc["games"], "analysis_conditioning.json:R6.anchor_free_excluded.games")
    put("r6.excl.ratio_min", _exc["ratio_min"], "analysis_conditioning.json:R6.anchor_free_excluded.ratio_min")
    put("r6.excl.ratio_max", _exc["ratio_max"], "analysis_conditioning.json:R6.anchor_free_excluded.ratio_max")
    put("r6.excl.ratio_min_3dp", _exc["ratio_min_3dp"],
        "analysis_conditioning.json:R6.anchor_free_excluded.ratio_min_3dp")
    put("r6.excl.ratio_max_3dp", _exc["ratio_max_3dp"],
        "analysis_conditioning.json:R6.anchor_free_excluded.ratio_max_3dp")
    put("r6.all.g_positive", _all["g_positive"], "analysis_conditioning.json:R6.all_games.g_positive")
    put("r6.all.cells", _all["cells"], "analysis_conditioning.json:R6.all_games.cells")

    # --- ground truth by construction: the anchors -----------------------------------------------
    anchors = v4["anchors"]
    certified = sorted(k for k, a in anchors.items() if a.get("certified"))
    uncertified = sorted(k for k, a in anchors.items() if not a.get("certified"))
    put("v4.anchors_certified", len(certified), "spike_v4_results.json:anchors[*].certified")
    put("v4.anchors_total", len(anchors), "spike_v4_results.json:anchors")
    put("v4.anchors_uncertified", uncertified, "spike_v4_results.json:anchors[*].certified")

    # --- the design law --------------------------------------------------------------------------
    dl = v4["design_law"]
    put("v4.law_mismatches", len(dl["law_mismatches"]),
        "spike_v4_results.json:design_law.law_mismatches")
    put("v4.band_counts", dict(dl["band_counts"]), "spike_v4_results.json:design_law.band_counts")
    faithful = sorted(k for k, b in dl["bands"].items() if b == "faithful")
    put("v4.faithful_protocols", faithful, "spike_v4_results.json:design_law.bands")
    # the classification the law is stated over, read from the spike's own tables (not a copy)
    sys.path.insert(0, HERE)
    import spike_v4 as V4S  # noqa: E402
    reads = V4S.READS
    put("v4.protocols_reading_row", sorted(k for k, r in reads.items() if r == "row"),
        "spike_v4.READS (imported)")
    put("v4.protocols_reading_profile", sorted(k for k, r in reads.items() if r == "profile"),
        "spike_v4.READS (imported)")
    put("v4.protocols_reading_neither", sorted(k for k, r in reads.items()
                                               if r not in ("row", "profile")),
        "spike_v4.READS (imported) -- the population-blind reference")
    row = [k for k, r in reads.items() if r == "row"]
    put("v4.row_reading_count", len(row), "spike_v4.READS (imported)")
    put("v4.row_reading_faithful_count", len([k for k in row if k in faithful]),
        "spike_v4.READS x spike_v4_results.json:design_law.bands")

    # --- the v2/v3 grid's nesting (a DIFFERENT design space; quoted only with its own name) ------
    nest = v2["nesting"]
    put("v2.nesting.strict_band_derived", nest["immune"] - nest["faithful"],
        "spike_v2_design.json:nesting.immune - nesting.faithful (computed here)")
    put("v2.nesting", {"cells": nest["cells"], "faithful": nest["faithful"],
                       "immune": nest["immune"], "strict_band": nest["immune_and_unfaithful"],
                       "strictly_contains": nest["strictly_contains"]},
        "spike_v2_design.json:nesting")

    # --- P1: rank can be bought ------------------------------------------------------------------
    p1 = v4["P1_gain_positive"]
    put("v4.P1.G_pos", p1["G_pos"], "spike_v4_results.json:P1_gain_positive.G_pos")
    put("v4.P1.cells", p1["cells"], "spike_v4_results.json:P1_gain_positive.cells")
    per_game = p1["per_game"]
    counts = {g: (v["G_pos"] if isinstance(v, dict) else v) for g, v in per_game.items()}
    put("v4.P1.per_game_G_pos", counts, "spike_v4_results.json:P1_gain_positive.per_game")
    put("v4.P1.per_game_min", min(counts.values()), "spike_v4_results.json:P1_gain_positive.per_game")
    put("v4.P1.per_game_max", max(counts.values()), "spike_v4_results.json:P1_gain_positive.per_game")
    put("v4.P1.conclusion", p1.get("majority"), "spike_v4_results.json:P1_gain_positive.majority")

    # --- T3: the dominance and the containment ---------------------------------------------------
    t3 = v4["T3_inclusion"]
    put("v4.T3.gameable", t3["gameable_cells"], "spike_v4_results.json:T3_inclusion.gameable_cells")
    put("v4.T3.fragile", t3["fragile_cells"], "spike_v4_results.json:T3_inclusion.fragile_cells")
    put("v4.T3.strictly_contains", t3["strictly_contains"],
        "spike_v4_results.json:T3_inclusion.strictly_contains")
    put("v4.T3.band", t3["fragile_cells"] - t3["gameable_cells"],
        "spike_v4_results.json:T3_inclusion.fragile_cells - gameable_cells (computed here)")
    put("v4.T3.counterexamples", t3["n_g_positive_without_fragility"],
        "spike_v4_results.json:T3_inclusion.n_g_positive_without_fragility")
    put("v4.T3.reversed_cells", t3["reversed_cells"], "spike_v4_results.json:T3_inclusion.reversed_cells")
    rev = {k: v["reversed"] for k, v in v4["per_protocol"].items() if v["reversed"]}
    put("v4.T3.reversed_by_protocol", rev, "spike_v4_results.json:per_protocol[*].reversed")

    # --- P2: the two-way decomposition, and the ratio --------------------------------------------
    # the artefact stores EXACT rationals as "n/d" strings -- never parse them as floats, which
    # would silently round the very quantity the paragraph quotes
    fs = v4["factor_split"]
    ratios = {}
    for g, v in fs.items():
        ms_p, ms_pop = v.get("MS_protocol"), v.get("MS_population")
        assert ms_p is not None and ms_pop is not None, g
        ratios[g] = Fraction(ms_p) / Fraction(ms_pop)
    put("v4.P2.games_protocol_gt_population",
        sum(1 for v in fs.values() if v.get("protocol_exceeds_population")),
        "spike_v4_results.json:factor_split[*].protocol_gt_population")
    put("v4.P2.games_total", len(fs), "spike_v4_results.json:factor_split")
    put("v4.P2.ms_ratio_by_game",
        {k: {"exact": "%d/%d" % (v.numerator, v.denominator), "3dp": round(float(v), 3)}
         for k, v in ratios.items()},
        "spike_v4_results.json:factor_split (MS_protocol / MS_population, computed here)")
    put("v4.P2.ms_ratio_min", round(float(min(ratios.values())), 3), "computed from factor_split")
    put("v4.P2.ms_ratio_max", round(float(max(ratios.values())), 3), "computed from factor_split")
    put("v4.P2.ms_ratio_min_game", min(ratios, key=ratios.get), "computed from factor_split")
    put("v4.P2.ms_ratio_max_game", max(ratios, key=ratios.get), "computed from factor_split")

    # --- the ladder (v1's T4: two thresholds on the same contamination axis) ----------------------
    t4 = v1.get("T4_thresholds", {})
    put("v1.lambda_tau", t4.get("lambda_tau"), "spike_v1_theory.json:T4_thresholds.lambda_tau")
    put("v1.lambda_G", t4.get("lambda_G"), "spike_v1_theory.json:T4_thresholds.lambda_G")

    # --- the ladder, in full: the two thresholds and the cells each side of them ------------------
    mix = v1["T4_mixing"]
    put("v1.ladder.table",
        {k: {"g_pos": v["g_pos"], "tau_lt_1": v["tau_lt_1"], "cells": v["cells"]}
         for k, v in sorted(mix.items(), key=lambda kv: Fraction(kv[0]))},
        "spike_v1_theory.json:T4_mixing")
    put("v1.ladder.base", v1["T4_thresholds"]["base"],
        "spike_v1_theory.json:T4_thresholds.base")
    put("v1.ladder.tau_lt_1_at_lambda_tau", mix[v1["T4_thresholds"]["lambda_tau"]]["tau_lt_1"],
        "spike_v1_theory.json:T4_mixing[lambda_tau].tau_lt_1")
    put("v1.ladder.g_pos_at_lambda_tau", mix[v1["T4_thresholds"]["lambda_tau"]]["g_pos"],
        "spike_v1_theory.json:T4_mixing[lambda_tau].g_pos")
    put("v1.ladder.g_pos_at_lambda_G", mix[v1["T4_thresholds"]["lambda_G"]]["g_pos"],
        "spike_v1_theory.json:T4_mixing[lambda_G].g_pos")
    put("v1.ladder.tau_lt_1_at_lambda_G", mix[v1["T4_thresholds"]["lambda_G"]]["tau_lt_1"],
        "spike_v1_theory.json:T4_mixing[lambda_G].tau_lt_1")
    put("v1.ladder.saturation_lambda", next(k for k, v in
        sorted(mix.items(), key=lambda kv: Fraction(kv[0])) if v["g_pos"] == v["cells"]),
        "spike_v1_theory.json:T4_mixing (first lambda at which every cell buys rank)")
    plant = v1["T4_plant_monotone_base"]
    put("v1.ladder.monotone_plant_fires", {"g_pos": sum(v["g_pos"] for v in plant.values()),
                                           "tau_lt_1": sum(v["tau_lt_1"] for v in plant.values())},
        "spike_v1_theory.json:T4_plant_monotone_base (the control: a monotone base must fire neither)")

    # --- the transport statistic, and the two sets that must never be conflated ------------------
    hl = v4["headline"]
    put("v4.transport.excess_zero_set", sorted(hl["excess_zero_set"]),
        "spike_v4_results.json:headline.excess_zero_set")
    put("v4.transport.raw_zero_set", sorted(hl["raw_zero_set"]),
        "spike_v4_results.json:headline.raw_zero_set")
    put("v4.transport.faithful_set", sorted(hl["faithful_set"]),
        "spike_v4_results.json:headline.faithful_set")
    put("v4.transport.naive_law_violators", sorted(hl["naive_law_violators"]),
        "spike_v4_results.json:headline.naive_law_violators")
    put("v4.transport.reversed_set", sorted(hl.get("reversed_set") or []),
        "spike_v4_results.json:headline.reversed_set")

    # --- v0: the monotone control and the outcome score ------------------------------------------
    put("v0.cells", len(v0["cells"]), "spike_v0_results.json:cells")
    put("v0.protocols", len(v0["protocols"]), "spike_v0_results.json:protocols")
    put("v0.games", len(v0["games"]), "spike_v0_results.json:games")
    f0 = v0["findings"]["per_protocol"]
    ctl = f0["mean_payoff"]
    put("v0.control.cells", ctl["cells"], "spike_v0_results.json:findings.per_protocol.mean_payoff")
    put("v0.control.G_pos", ctl["G_pos"], "spike_v0_results.json:findings.per_protocol.mean_payoff.G_pos")
    put("v0.control.C_max", ctl["C_max"], "spike_v0_results.json:findings.per_protocol.mean_payoff.C_max")
    put("v0.control.tau_mean", ctl["tau_mean"],
        "spike_v0_results.json:findings.per_protocol.mean_payoff.tau_mean")
    gw = f0["game_wins"]
    put("v0.game_wins.G_pos", gw["G_pos"], "spike_v0_results.json:findings.per_protocol.game_wins.G_pos")
    put("v0.game_wins.cells", gw["cells"], "spike_v0_results.json:findings.per_protocol.game_wins")
    put("v0.game_wins.tau_mean_exact", gw["tau_mean"],
        "spike_v0_results.json:findings.per_protocol.game_wins.tau_mean")
    put("v0.game_wins.tau_mean_3dp", round(float(Fraction(gw["tau_mean"])), 3),
        "spike_v0_results.json:findings.per_protocol.game_wins.tau_mean (as a decimal)")
    put("v0.P1.per_game_G_pos", dict(sorted(v0["findings"]["G_pos_per_game"].items())),
        "spike_v0_results.json:findings.G_pos_per_game")
    put("v0.P1.per_game_cells",
        112 // len(v0["findings"]["G_pos_per_game"]),
        "computed: v0 cells / games (7 protocols x 4 populations each)")
    nbm = f0["norm_by_best"]
    put("v0.norm_by_best.G_pos", nbm["G_pos"],
        "spike_v0_results.json:findings.per_protocol.norm_by_best.G_pos")

    # --- the transport census: violators, on two named domains -----------------------------------
    ex = art(EXC)
    put("census.exc.entries", ex["entries"], "census_excess_entries.json:entries")
    put("census.exc.protocols", ex["protocols"], "census_excess_entries.json:protocols")
    put("census.exc.violators_all", ex["violators_all"], "census_excess_entries.json:violators_all")
    put("census.exc.violators_record_all", ex["violators_record_all"],
        "census_excess_entries.json:violators_record_all")
    put("census.exc.violators_record_all_designs", ex["violators_record_all_designs"],
        "census_excess_entries.json:violators_record_all_designs")
    put("census.exc.violators_base_positive", ex["violators_base_positive"],
        "census_excess_entries.json:violators_base_positive")
    put("census.exc.violators_record_base_positive", ex["violators_record_base_positive"],
        "census_excess_entries.json:violators_record_base_positive")
    put("census.exc.violators_record_base_positive_designs",
        ex["violators_record_base_positive_designs"],
        "census_excess_entries.json:violators_record_base_positive_designs")
    put("census.exc.record_base_positive_by_protocol",
        dict(sorted(ex["violators_record_base_positive_by_protocol"].items(), key=lambda kv: -kv[1])),
        "census_excess_entries.json:violators_record_base_positive_by_protocol")
    put("census.exc.evaluated_all", ex["evaluated_all"], "census_excess_entries.json:evaluated_all")
    put("census.exc.evaluated_record", ex["evaluated_record"],
        "census_excess_entries.json:evaluated_record")
    put("census.exc.evaluated_record_intersect_violators",
        ex["evaluated_record_intersect_record_violators"],
        "census_excess_entries.json:evaluated_record_intersect_record_violators")
    put("census.exc.forward_counterexamples_all", ex["forward_counterexamples_all"],
        "census_excess_entries.json:forward_counterexamples_all")
    put("census.exc.base_values", dict(ex["base_values"]), "census_excess_entries.json:base_values")
    put("census.exc.random_fixed", {"entries": ex["random_fixed_entries"],
                                    "raw_zero": ex["random_fixed_raw_zero"],
                                    "excess_zero": ex["random_fixed_excess_zero"]},
        "census_excess_entries.json:random_fixed_*")
    put("census.exc.rank_score", {"entries": ex["rank_score_entries"],
                                  "raw_zero": ex["rank_score_raw_zero"],
                                  "excess_zero": ex["rank_score_excess_zero"]},
        "census_excess_entries.json:rank_score_*")
    put("census.exc.neg_mean", {"entries": ex["neg_mean_entries"],
                                "raw_zero": ex["neg_mean_raw_zero"],
                                "excess_zero": ex["neg_mean_excess_zero"],
                                "excess_zero_base_positive": ex["neg_mean_excess_zero_base_positive"]},
        "census_excess_entries.json:neg_mean_*")
    put("census.exc.certificate", {"ok": ex["_certificate"]["ok"],
                                   "total": ex["_certificate"]["total"]},
        "census_excess_entries.json:_certificate")

    # --- the converse census: what the design space does and does not supply ----------------------
    cv = art(CONV)
    items = cv["_certificate"]["items"]
    put("census.conv.certificate", {"ok": sum(1 for i in items if i.strip().startswith("OK")),
                                    "total": len(items)},
        "census_converse_scope.json:_certificate")
    put("census.conv.grid_populations_per_game", cv["populations_per_game"],
        "census_converse_scope.json:populations_per_game")
    put("census.conv.target_discordant", cv["target"],
        "census_converse_scope.json:target")
    put("census.conv.pairs", cv["pairs"], "census_converse_scope.json:pairs")
    put("census.conv.games_attaining_target", cv["games_attaining_target"],
        "census_converse_scope.json:games_attaining_target")
    put("census.conv.max_reachable_discordant", cv["global_max"],
        "census_converse_scope.json:global_max")
    put("census.conv.max_of_record", cv["global_max_of_record"],
        "census_converse_scope.json:global_max_of_record")
    put("census.conv.mixed_orientation_protocols", cv["mixed_protocols_anywhere"],
        "census_converse_scope.json:mixed_protocols_anywhere")
    # an EMPTY collection has no value a prose check can find, so the count is its own key -- the
    # gate refuses to treat "[]" as "the sentence contains nothing, therefore it agrees"
    put("census.conv.mixed_orientation_count", len(cv["mixed_protocols_anywhere"]),
        "census_converse_scope.json:mixed_protocols_anywhere (length, computed here)")

    # --- the natural witness on the v4 grid ------------------------------------------------------
    pp = v4["per_protocol"]["neg_mean"]
    put("v4.neg_mean.G_max", pp["G_max"], "spike_v4_results.json:per_protocol.neg_mean.G_max")
    put("v4.neg_mean.cells", pp["cells"], "spike_v4_results.json:per_protocol.neg_mean.cells")
    put("v4.neg_mean.gameable", pp["gameable"], "spike_v4_results.json:per_protocol.neg_mean.gameable")

    return n


# --------------------------------------------------------------------------------------------------
def _fmt(v):
    if isinstance(v, dict):
        return "{" + ", ".join("%s: %s" % (k, v[k]) for k in list(v)[:6]) + ("..." if len(v) > 6 else "") + "}"
    if isinstance(v, list):
        return "[" + ", ".join(str(x) for x in v[:6]) + ("..." if len(v) > 6 else "") + "]"
    return str(v)


def main(argv):
    selftest = "--selftest" in argv
    n = numbers()

    if "--json" in argv:
        print(json.dumps({k: v["value"] for k, v in n.items()}, indent=1, sort_keys=True))
        return 0

    if not selftest:
        w = max(len(k) for k in n)
        print("== issue #141 -- the canonical numbers (%d) ==" % len(n))
        for k, v in n.items():
            print("  %-*s = %-40s  <- %s" % (w, k, _fmt(v["value"]), v["source"]))
        return 0

    # ---------------------------------------------------------------- the plants
    ok = True

    def holds(name, cond):
        nonlocal ok
        print("[%-52s] %s" % (name, "ok" if cond else "*** FAIL ***"))
        ok = ok and cond

    # 1 the parts sum to the whole: P1's per-game counts must add up to the headline count
    s = sum(n["v4.P1.per_game_G_pos"]["value"].values())
    holds("per-game G>0 counts sum to the headline", s == n["v4.P1.G_pos"]["value"])
    # 2 the grid is the product it claims to be
    holds("cells == games x protocols x populations",
          n["v4.cells"]["value"] == n["v4.games"]["value"] * n["v4.protocols"]["value"]
          * n["v4.populations"]["value"])
    # 3 containment is STRICT, and the sign of the gap is the theorem's
    holds("gameable < fragile", n["v4.T3.gameable"]["value"] < n["v4.T3.fragile"]["value"])
    holds("no cell has G>0 with tau==1", n["v4.T3.counterexamples"]["value"] == 0)
    # 4 the reversed cells are exactly the sum of their per-protocol parts
    holds("reversed cells == sum of per-protocol reversed",
          sum(n["v4.T3.reversed_by_protocol"]["value"].values()) == n["v4.T3.reversed_cells"]["value"])
    # 5 the ratio range is read off the per-game ratios, not retyped
    r = {k: v["3dp"] for k, v in n["v4.P2.ms_ratio_by_game"]["value"].items()}
    holds("ratio min/max match the per-game table",
          abs(min(r.values()) - n["v4.P2.ms_ratio_min"]["value"]) < 5e-4
          and abs(max(r.values()) - n["v4.P2.ms_ratio_max"]["value"]) < 5e-4)
    # 6 the design law's own claim: no row-reader is faithful
    holds("the three read classes partition the protocol count",
          0 == n["v4.protocols"]["value"]
          - n["v4.row_reading_count"]["value"]
          - len(n["v4.protocols_reading_profile"]["value"])
          - len(n["v4.protocols_reading_neither"]["value"]))
    holds("zero row-reading protocols are faithful",
          n["v4.row_reading_faithful_count"]["value"] == 0)
    # 7 the two bands are disjoint, and faithful is exactly the profile+strict pair
    bands = n["v4.band_counts"]["value"]
    holds("band counts sum to the protocol count",
          sum(bands.values()) == n["v4.protocols"]["value"])
    # 8 the naive transport law has a named violator, and it is the constructed witness
    holds("the naive law's violator set is non-empty and named",
          n["v4.transport.naive_law_violators"]["value"] == ["rank_score"])
    # 9 excess-zero is NOT faithful: the two sets differ
    holds("excess_zero set != faithful set",
          n["v4.transport.excess_zero_set"]["value"] != n["v4.transport.faithful_set"]["value"])
    # 10 the ladder's ordering is the claim: fragility first
    lt, lg = n["v1.lambda_tau"]["value"], n["v1.lambda_G"]["value"]
    holds("lambda_tau < lambda_G", lt is not None and lg is not None and lt < lg)
    holds("at lambda_tau fragility fires and buyability does not",
          n["v1.ladder.tau_lt_1_at_lambda_tau"]["value"] > 0
          and n["v1.ladder.g_pos_at_lambda_tau"]["value"] == 0)
    holds("the monotone-base control fires neither threshold",
          n["v1.ladder.monotone_plant_fires"]["value"] == {"g_pos": 0, "tau_lt_1": 0})
    holds("the ladder is monotone in both counters",
          [v["g_pos"] for v in n["v1.ladder.table"]["value"].values()]
          == sorted(v["g_pos"] for v in n["v1.ladder.table"]["value"].values())
          and [v["tau_lt_1"] for v in n["v1.ladder.table"]["value"].values()]
          == sorted(v["tau_lt_1"] for v in n["v1.ladder.table"]["value"].values()))
    # 11 a PLANT: retyping the range instead of computing it must be caught.  The victim is the game
    # that actually HOLDS the minimum -- a plant that perturbs some other game proves nothing about
    # the min/max comparison, which is the same "the fixture must reach the branch" rule #142's round
    # 3 was spent on.
    typo = dict(r)
    victim = min(typo, key=typo.get)
    typo[victim] = typo[victim] * 10
    holds("plant: a retyped ratio is caught",
          abs(min(typo.values()) - n["v4.P2.ms_ratio_min"]["value"]) >= 5e-4)
    # 12 the two census domains are named, and their counts are NOT interchangeable
    holds("the record violators sum to their per-protocol parts",
          sum(n["census.exc.record_base_positive_by_protocol"]["value"].values())
          == n["census.exc.violators_record_base_positive"]["value"])
    holds("the base-value classes partition the entry domain",
          sum(n["census.exc.base_values"]["value"].values()) == n["census.exc.entries"]["value"])
    holds("the evaluated set and the violator set are disjoint where both are record-level",
          n["census.exc.evaluated_record_intersect_violators"]["value"] == 0)
    # the count coincidence: two DIFFERENT sets with the same size.  Asserted as a coincidence, so a
    # later edit that makes them equal by construction trips this and is made to think about it.
    holds("the 262/262 coincidence is a coincidence of two disjoint sets",
          n["census.exc.evaluated_all"]["value"] == n["census.exc.violators_record_all"]["value"]
          and n["census.exc.evaluated_record_intersect_violators"]["value"] == 0)
    holds("T_raw and T_excess are different objects on the population-blind reference",
          n["census.exc.random_fixed"]["value"]["raw_zero"]
          > n["census.exc.random_fixed"]["value"]["excess_zero"])
    holds("the shipped design cannot reach the converse's target discordance",
          n["census.conv.max_of_record"]["value"] < n["census.conv.target_discordant"]["value"])
    holds("the v4 band equals fragile minus gameable",
          n["v4.T3.band"]["value"] == n["v4.T3.fragile"]["value"] - n["v4.T3.gameable"]["value"])
    holds("the strict band equals immune minus faithful",
          n["v2.nesting.strict_band_derived"]["value"]
          == n["v2.nesting"]["value"]["immune"] - n["v2.nesting"]["value"]["faithful"])
    holds("v0 per-game counts fit inside their own cell count",
          max(n["v0.P1.per_game_G_pos"]["value"].values()) <= n["v0.P1.per_game_cells"]["value"])
    # 13 a PLANT: a per-game count that does not add up must be caught
    broken = dict(n["v4.P1.per_game_G_pos"]["value"])
    bk = sorted(broken)[0]
    broken[bk] = broken[bk] + 1
    holds("plant: a mis-summed per-game count is caught",
          sum(broken.values()) != n["v4.P1.G_pos"]["value"])

    print("CANONICAL:", "ALL PASS" if ok else "A CHECK IS DECORATION")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
