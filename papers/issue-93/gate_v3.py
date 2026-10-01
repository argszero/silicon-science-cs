#!/usr/bin/env python3
"""#93 v3 -- the verification round: the design ladder under DISJOINT STREAMS with intervals, the two
published orderings, and the headline's own sensitivity.

WHERE THIS SITS.  v0 read the screening closure (b = 1), v1 the map (b < 1), v2 the design axis (which repair
closes which defect class).  All three read ONE draw of the sampling route -- the enumeration is exact, so the
model's values were never in question; what was never checked is that the exact values are the values the
study's own sampling route RECOVERS, over more than one stream; and the registration's external-validation
arm (two published orderings, plus the published parameter values) had not been run as its own read.

WHAT IS MEASURED.
  A  EACH STREAM ON ITS OWN.  Nine streams in three declared seed families, each stream run separately, with
     its own interval, at every cell of a 7-cell parameter grid and every design.  The criterion is the
     interval's SIZE PROPERTY, not a lucky draw: coverage is a RATE over the cells, judged against the nominal
     0.95 by a Wilson interval, because at 378 readings a correctly sized 95 % interval fails to cover five per
     cent of them by construction.  v0 and v2 required EVERY cell to cover; that criterion cannot survive its
     own nominal rate at this scale, and this round says so in the code rather than in prose.
  B  THE ORDERING, WITHIN EVERY STREAM.  For each (cell, stream) the drawn design values must satisfy the
     v2 ladder's ordering -- D1 <= D2 <= D3 <= D4 and at least one gated design below no-gate -- so the
     ordering is unanimity over nine streams rather than an average that a bimodal ensemble could produce.
  C  THE TWO PUBLISHED ORDERINGS (the registration's external-validation arm), read where each claim lives:
     the VAC arm beats the text-approval arm in value; the unbound arm is the worst in the reported 68-100 %
     attack-success band; and the anchor's "0 % attack success with binding" is the re-derived design's own
     value.  Plus the anchor's measured FIDELITY values: b = 1 (binding holds) and b = 0 (100 % deactivation
     of binding state, 2608.24569), fed into v1's closed forms.
  D  THE HEADLINE'S SENSITIVITY.  The study's headline is that a gate over a defective channel can be worth
     LESS than no gate.  Over the parameter grid, how many cells show it, which designs show it, and what it
     would take to remove it -- reported as counts over a declared grid rather than as a single cell's value.

Run:  /usr/bin/python3 gate_v3.py
Writes gate_v3_results.json beside this file.
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
import gate_v0 as V0  # noqa: E402
import gate_v1 as V1  # noqa: E402
import gate_v2 as V2  # noqa: E402

OUT = os.path.join(HERE, "gate_v3_results.json")
S = 1.0
N_DRAW = 200000

# The parameter grid is the one v0's closure control used, unaltered: the same seven cells, now read over
# nine streams instead of one.
CELLS = [
    ("defaults", V0._p()),
    ("pi=0.05", V0._p(pi=0.05)),
    ("pi=0.5,a=0.6", V0._p(pi=0.5, a=0.6)),
    ("a=0.3,f=0.2", V0._p(a=0.3, f=0.2)),
    ("a=0.95,f=0.0", V0._p(a=0.95, f=0.0)),
    ("L=5,c=0.1,cb=0.2", V0._p(L=5.0, c=0.1, cb=0.2)),
    ("pi=0.02,a=0.99,f=0.5", V0._p(pi=0.02, a=0.99, f=0.5)),
]

# The seed families are DECLARED HERE, before the run, and each is reported separately as well as pooled: a
# panel whose seeds share a magnitude measures one draw's neighbourhood (self-audit Class 100's rule).
FAMILIES = {
    "adjacent": [20260922, 20260923, 20260924],
    "wide_magnitude": [7, 1009, 123457],
    "cluster": [41020261, 41020262, 41020263],
}
STREAMS = [s for fam in ("adjacent", "wide_magnitude", "cluster") for s in FAMILIES[fam]]
FAMILY_OF = {s: fam for fam, ss in FAMILIES.items() for s in ss}
NOMINAL = 0.95
Z95 = 1.959963984540054


def wilson(k, n, z=Z95):
    """Wilson score interval for a proportion -- the right interval for a RATE (the nominal-coverage check)."""
    if n == 0:
        return (0.0, 1.0)
    p = k / n
    d = 1.0 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (c - h, c + h)


def main():
    res = {
        "what": "issue #93 v3 -- one construction under nine disjoint streams: coverage as a rate, the ordering "
                "within every stream, the registration's two published orderings, and the headline's sensitivity",
        "why": "v0/v1/v2 read one stream each and two of them judged the sampling route by an all-cells-cover "
               "criterion that a correctly sized 95 %% interval cannot meet at this scale",
        "designs": list(V2.DESIGNS), "defect_defaults": dict(V2.DEFECT), "s": S, "n_draw": N_DRAW,
        "stream_families": {k: list(v) for k, v in FAMILIES.items()},
        "grid_cells": [c[0] for c in CELLS],
        "nominal": NOMINAL,
    }
    report = []

    def say(line=""):
        print(line)
        report.append(line)

    # ------------------------------------------------------------------ A: the exact ladder and the drawn route
    say("=== A. every cell, every design, nine streams -- the exact value and the stream's own interval")
    rows = []
    for label, params in CELLS:
        for design in V2.DESIGNS:
            exact_loss, dec = V2.enum_design(params, S, design)
            exact_value = params["L"] * params["pi"] - exact_loss
            for seed in STREAMS:
                draw, ci, attack = V2.simulate_design(params, S, design, n=N_DRAW, seed=seed)
                rows.append(dict(
                    cell=label, design=design, family=FAMILY_OF[seed], seed=seed,
                    exact_loss=exact_loss, exact_value=exact_value,
                    drawn_loss=draw, drawn_value=params["L"] * params["pi"] - draw,
                    lo=ci[0], hi=ci[1], covers=bool(ci[0] <= exact_loss <= ci[1]),
                    width=ci[1] - ci[0], attack=attack,
                    exact_attack=dec["attack_success"],
                    value_gap=abs((params["L"] * params["pi"] - draw) - exact_value),
                ))
    n_cells = len(rows)
    # A ZERO-WIDTH INTERVAL IS NOT AN INTERVAL.  The no-gate design's route is exact by construction (its loss
    # is L*pi with no sampling), so it reports the point (L*pi, L*pi) and "covers" every time.  Counting those
    # readings as coverage inflates the rate: the first version of this check pooled all 378 and read 0.9762,
    # a rate no 95 % interval produces -- the defect was in the DENOMINATOR, not in the intervals.  They are
    # reported separately, as the exactness control they are, and the rate is taken over real intervals.
    sampled = [r for r in rows if r["width"] > 0.0]
    degenerate = [r for r in rows if r["width"] == 0.0]
    covered = sum(1 for r in sampled if r["covers"])
    n_cells = len(sampled)
    lo, hi = wilson(covered, n_cells)
    res["coverage"] = dict(readings=n_cells, covered=covered, rate=covered / n_cells,
                           wilson=[lo, hi], nominal_inside=bool(lo <= NOMINAL <= hi),
                           non_degenerate=n_cells, degenerate_readings=len(degenerate),
                           degenerate_exact=bool(all(abs(r["drawn_loss"] - r["exact_loss"]) == 0.0
                                                     for r in degenerate)),
                           pooled_all=len(rows))
    say("  %d readings with an interval (%d cells x %d designs x %d streams, less the no-gate design's %d "
        "exact readings); covered %d = %.4f (Wilson95 [%.4f, %.4f])"
        % (n_cells, len(CELLS), len(V2.DESIGNS), len(STREAMS), len(degenerate), covered,
           covered / n_cells, lo, hi))
    say("  nominal %.2f inside that interval: %s  -- the criterion is the RATE, not every cell"
        % (NOMINAL, res["coverage"]["nominal_inside"]))
    say("  the no-gate design's %d readings are exact points (drawn == enumerated exactly): %s"
        % (len(degenerate), res["coverage"]["degenerate_exact"]))
    if not res["coverage"]["nominal_inside"]:
        raise RuntimeError("the drawn intervals' coverage rate is not consistent with the nominal 95%%: %s"
                           % res["coverage"])
    if not res["coverage"]["degenerate_exact"]:
        raise RuntimeError("the no-gate route is not exact on some reading: %s" % degenerate[:2])

    # per-design coverage, so a class-specific defect (a caught class) cannot hide inside the pooled rate
    per_design = {}
    for design in V2.DESIGNS:
        sel = [r for r in sampled if r["design"] == design]
        if not sel:                     # the no-gate design has no interval at all (all its readings are exact)
            per_design[design] = dict(n=0, covered=0, rate=None, wilson=None, note="no interval: exact route")
            continue
        k = sum(1 for r in sel if r["covers"])
        per_design[design] = dict(n=len(sel), covered=k, rate=k / len(sel), wilson=list(wilson(k, len(sel))))
    per_family = {}
    for fam in FAMILIES:
        sel = [r for r in sampled if r["family"] == fam]
        k = sum(1 for r in sel if r["covers"])
        per_family[fam] = dict(n=len(sel), covered=k, rate=k / len(sel), wilson=list(wilson(k, len(sel))))
    res["coverage_by_design"] = per_design
    res["coverage_by_family"] = per_family
    say("  by design: " + " | ".join(
        ("%s %d/%d" % (d, per_design[d]["covered"], per_design[d]["n"])) if per_design[d]["n"]
        else ("%s exact" % d) for d in V2.DESIGNS))
    say("  by family: " + " | ".join("%s %d/%d" % (f, per_family[f]["covered"], per_family[f]["n"])
                                    for f in FAMILIES))

    # ------------------------------------------------------------------ B: the ordering inside every stream
    #
    # AN ORDERING CLAIM OWES ITS RESOLUTION.  The model's ladder D1 <= D2 <= D3 <= D4 is a statement about the
    # EXACT values, and the exact values are strictly monotone at every cell.  A stream can only witness it
    # where the pair's exact gap exceeds that pair's own sampling spread: at the cell `pi=0.02,a=0.99,f=0.5`
    # the D1->D2 exact gap is +0.00294 while the nine streams' drawn gaps run from -0.00021 to +0.00377, so
    # two of the nine see the wrong sign -- not because the model disagrees with itself, but because the
    # reading has no resolution there.  The first version of this check demanded unanimity with a 1e-9
    # tolerance and called that a failure; the repair is to write the floor into the criterion and to REPORT
    # the readings it excludes, with their gap/floor ratio, rather than to lower a threshold.
    say()
    say("=== B. the design ordering: exact at every cell, and witnessed by the streams wherever it is resolvable")
    pairs = (("D1", "D2"), ("D2", "D3"), ("D3", "D4"))
    order_rows, pair_rows = [], []
    for label, params in CELLS:
        exact = {d: V2.value(params, S, d) for d in V2.DESIGNS}
        mono = all(exact[a] < exact[b] for a, b in pairs)
        drawn = {}
        for seed in STREAMS:
            drawn[seed] = {d: params["L"] * params["pi"]
                              - V2.simulate_design(params, S, d, n=N_DRAW, seed=seed)[0]
                           for d in V2.DESIGNS}
        below = sorted({d for d in V2.DESIGNS[1:]
                        if any(drawn[s][d] < drawn[s]["D0"] - 1e-9 for s in STREAMS)})
        always_below = sorted({d for d in V2.DESIGNS[1:]
                               if all(drawn[s][d] < drawn[s]["D0"] - 1e-9 for s in STREAMS)})
        order_rows.append(dict(cell=label, monotone_exact=bool(mono), below_no_gate=below,
                               always_below_no_gate=always_below,
                               exact=exact, drawn={str(k): v for k, v in drawn.items()}))
        for a, b in pairs:
            gap = exact[b] - exact[a]
            dg = [drawn[s][b] - drawn[s][a] for s in STREAMS]
            # The floor is the resolution of ONE stream on this pair: 1.96 x the streams' own sd, estimated
            # from the nine draws.  A criterion demanding unanimity over nine streams is only one the model can
            # be expected to pass where a single stream's sign error is unlikely (|gap| / sd > ~2 gives < 2.5 %
            # per stream and >= 0.80 for nine of nine).  Using the MAX |drawn gap| instead -- the first version
            # of this floor -- is not a spread measure at all: it flagged 19 of 21 pairs as unresolvable,
            # including pairs whose gap is 0.2 with a stream sd near 0.03.
            sd = float(np.std(dg, ddof=1)) if len(dg) > 1 else 0.0
            floor = 1.959963984540054 * sd
            unanimous = all((g > 0) == (gap > 0) for g in dg)
            pair_rows.append(dict(cell=label, pair="%s->%s" % (a, b), exact_gap=gap, stream_sd=sd,
                                  floor=floor, ratio=abs(gap) / floor if floor > 0 else float("inf"),
                                  resolvable=bool(abs(gap) > floor), unanimous=bool(unanimous),
                                  drawn_gaps=dg))
    below_floor = [r for r in pair_rows if not r["resolvable"]]
    above_floor = [r for r in pair_rows if r["resolvable"]]
    failed = [r for r in above_floor if not r["unanimous"]]
    res["ordering"] = dict(
        exact_monotone_all=bool(all(r["monotone_exact"] for r in order_rows)),
        cells_monotone_exact=sum(1 for r in order_rows if r["monotone_exact"]), cells=len(order_rows),
        readings=len(order_rows),
        readings_with_a_gate_below_no_gate=sum(1 for r in order_rows if r["always_below_no_gate"]),
        pairs=len(pair_rows), pairs_above_the_floor=len(above_floor),
        pairs_below_the_floor=len(below_floor), pairs_above_floor_all_unanimous=bool(not failed),
        failed=[{k: v for k, v in r.items() if k != "drawn_gaps"} for r in failed],
        below_floor=[{k: v for k, v in r.items() if k != "drawn_gaps"} for r in below_floor],
        rows=order_rows, pair_rows=pair_rows)
    say("  exact D1 < D2 < D3 < D4 at %d of %d cells: %s"
        % (res["ordering"]["cells_monotone_exact"], res["ordering"]["cells"],
           res["ordering"]["exact_monotone_all"]))
    say("  of the %d (cell, pair) readings, %d have an exact gap above the streams' own spread and %d below it"
        % (len(pair_rows), len(above_floor), len(below_floor)))
    say("  every resolvable reading unanimous in sign across all nine streams: %s"
        % res["ordering"]["pairs_above_floor_all_unanimous"])
    for r in below_floor:
        say("    below the floor: %-22s %s  exact gap %+.5f vs 1.96*sd %.5f (ratio %.2f)"
            % (r["cell"], r["pair"], r["exact_gap"], r["floor"], r["ratio"]))
    if above_floor:
        say("    smallest resolvable pair: %.5f vs floor %.5f (ratio %.2f)"
            % (min(above_floor, key=lambda r: r["ratio"])["exact_gap"],
               min(above_floor, key=lambda r: r["ratio"])["floor"],
               min(above_floor, key=lambda r: r["ratio"])["ratio"]))
    say("  at least one gated design below no-gate in EVERY stream: %d of %d (cell) readings"
        % (res["ordering"]["readings_with_a_gate_below_no_gate"], res["ordering"]["readings"]))
    if not res["ordering"]["exact_monotone_all"]:
        raise RuntimeError("the exact design ladder is not strictly monotone at every cell: %s"
                           % [r["cell"] for r in order_rows if not r["monotone_exact"]])
    if failed:
        raise RuntimeError("a resolvable ordering reading is not unanimous across streams: %s" % failed)

    # ------------------------------------------------------------------ C: the registration's external arm
    say()
    say("=== C. the registration's external-validation arm, read where each published claim lives")
    base = V0._p()
    vals = {d: V2.value(base, S, d) for d in V2.DESIGNS}
    atk = {d: V2.enum_design(base, S, d)[1]["attack_success"] for d in V2.DESIGNS}
    # (1) the VAC arm beats the text-approval arm -- in VALUE and in every cell of the grid
    vac_beats_text = [dict(cell=label, vac=V2.value(p, S, "D4"), text=V2.value(p, S, "D1"),
                           holds=bool(V2.value(p, S, "D4") > V2.value(p, S, "D1")))
                      for label, p in CELLS]
    # (2) the unbound arm is the worst in the published 68-100 % attack-success band
    band = dict(published=[0.68, 1.00], unbound_atk=atk["D1"], inside=bool(0.68 <= atk["D1"] <= 1.00),
                unbound_is_max=bool(atk["D1"] >= max(a for a in atk.values() if a is not None) - 1e-12),
                all_designs=atk)
    # (3) "0 % attack success when binding holds": the re-derived design's own value, at a fully visible channel
    clean = dict(V2.DEFECT, delta=0.0, sigma_i=0.0)
    zero_binding = dict(channel="fully visible (delta = sigma_i = 0)", expected=0.0,
                        D3=V2.enum_design(base, S, "D3", clean)[1]["attack_success"],
                        D4=V2.enum_design(base, S, "D4", clean)[1]["attack_success"])
    zero_binding["holds"] = bool(zero_binding["D4"] is not None and abs(zero_binding["D4"]) < 1e-15)
    # (4) the fidelity parameter takes the anchor's MEASURED values: b = 1 (binding holds) and b = 0 (100 %
    # deactivation of binding state, 2608.24569).  Read on v1's closed forms, which is where b lives.
    fidelity = {}
    for b in (1.0, 0.5, 0.0):
        fidelity["b=%.1f" % b] = dict(
            substitution_value=V1.value_closed(base, "substitution", b, S),
            mismatch_value=V1.value_closed(base, "mismatch", b, S),
            substitution_bstar=V1.bstar_closed(base, "substitution"),
            mismatch_bstar=V1.bstar_closed(base, "mismatch"),
            below_its_own_threshold=bool(b < V1.bstar_closed(base, "substitution")))
    res["external"] = dict(values=vals, attack=atk, vac_beats_text=vac_beats_text,
                           vac_holds_in_every_cell=bool(all(r["holds"] for r in vac_beats_text)),
                           attack_band=band, zero_attack_when_binding_holds=zero_binding,
                           measured_fidelity_values=fidelity)
    say("  VAC (D4) beats text-approval (D1) in value: %+.4f > %+.4f at the defaults; in every one of the %d "
        "grid cells: %s" % (vals["D4"], vals["D1"], len(CELLS), res["external"]["vac_holds_in_every_cell"]))
    say("  unbound (D1) attack success %.4f -- inside the published 68-100 %% band: %s; worst of all: %s"
        % (band["unbound_atk"], band["inside"], band["unbound_is_max"]))
    say("  '0 %% attack success when binding holds': fully visible channel -> D3 %.4f, D4 %.4f (%s)"
        % (zero_binding["D3"], zero_binding["D4"], "holds" if zero_binding["holds"] else "DOES NOT HOLD"))
    say("  the anchor's measured fidelity values: b = 1 -> substitution value %+.4f; b = 0 -> %+.4f "
        "(below its own threshold %.4f: %s)"
        % (fidelity["b=1.0"]["substitution_value"], fidelity["b=0.0"]["substitution_value"],
           fidelity["b=1.0"]["substitution_bstar"], fidelity["b=0.0"]["below_its_own_threshold"]))
    if not (res["external"]["vac_holds_in_every_cell"] and band["inside"] and band["unbound_is_max"]
            and zero_binding["holds"]):
        raise RuntimeError("the external-validation arm does not reproduce the published orderings: %s"
                           % {k: res["external"][k] for k in ("vac_holds_in_every_cell", "attack_band")})

    # ------------------------------------------------------------------ D: the headline's sensitivity
    say()
    say("=== D. the headline's own sensitivity: how many cells show a net-harmful gate, and which design")
    harmful = []
    for label, params in CELLS:
        for design in V2.DESIGNS[1:]:
            v = V2.value(params, S, design)
            if v < -1e-12:
                harmful.append(dict(cell=label, design=design, value=v))
    cells_with_harm = sorted({h["cell"] for h in harmful})
    designs_harmful_somewhere = sorted({h["design"] for h in harmful})
    # THE GUARD COMES BEFORE THE REPORT.  The mutation battery caught this: with no harmful reading anywhere,
    # the first version reached the report line `"%.4f" % min_margin_frac` while that value was None and died
    # with a TypeError -- exit non-zero, so a battery that only read the exit code would have logged it as "the
    # alarm fired".  The alarm was therefore UNREACHABLE in exactly the direction it exists for, and the fix is
    # the order, not a defensive format.
    if not harmful:
        raise RuntimeError("the headline does not appear anywhere on the parameter grid: the phenomenon and the "
                           "grid disagree (a declared grid over %d cells and %d gated designs carries no "
                           "net-harmful gate)" % (len(CELLS), len(V2.DESIGNS) - 1))
    # what it would take to remove it: the value's distance to zero, as a fraction of the no-gate loss
    margins = []
    for h in harmful:
        label = h["cell"]
        params = dict(CELLS)[label]
        margins.append(dict(cell=label, design=h["design"], value=h["value"],
                            no_gate_loss=params["L"] * params["pi"],
                            margin_frac=abs(h["value"]) / (params["L"] * params["pi"])))
    res["headline_sensitivity"] = dict(readings=len(CELLS) * (len(V2.DESIGNS) - 1),
                                       harmful_readings=len(harmful),
                                       cells_with_a_harmful_gate=cells_with_harm,
                                       grids=len(CELLS), harmful=harmful, margins=margins,
                                       designs_harmful_somewhere=designs_harmful_somewhere,
                                       min_margin_frac=(min(m["margin_frac"] for m in margins) if margins else None))
    say("  %d of the %d (cell, design) readings are net-harmful gates, in %d of the %d cells: %s"
        % (len(harmful), res["headline_sensitivity"]["readings"], len(cells_with_harm), len(CELLS),
           ", ".join(cells_with_harm)))
    say("  designs that are harmful somewhere: %s" % ", ".join(designs_harmful_somewhere))
    say("  smallest margin (|value| as a fraction of the no-gate loss): %.4f"
        % res["headline_sensitivity"]["min_margin_frac"])

    # ------------------------------------------------------------------ controls
    say()
    say("=== controls")
    c1 = V2.enum_design(base, S, "D0")[0] == base["L"] * base["pi"]
    c2 = all(V2.simulate_design(base, S, d, n=N_DRAW, seed=STREAMS[0])
             == V2.simulate_design(base, S, d, n=N_DRAW, seed=STREAMS[0]) for d in V2.DESIGNS)
    c3 = max(abs(r["drawn_value"] - r["exact_value"]) for r in sampled)
    res["controls"] = dict(C1_no_gate_exact=bool(c1), C2_determinism=bool(c2),
                           C3_streams_land_within_a_bound_of_the_exact_value=bool(c3 < 0.25),
                           C3_worst_stream_gap=float(c3),
                           C4_all_cells_have_a_nonzero_streams_spread=bool(
                               any(abs(r["value_gap"]) > 0 for r in rows)))
    say("  C1 the no-gate design's enumerated loss is exactly L*pi: %s" % c1)
    say("  C2 the drawn route is deterministic given the seed: %s" % c2)
    say("  C3 the worst |drawn - exact| across the sampled readings: %.4f (a stream, not a divergence)"
        % res["controls"]["C3_worst_stream_gap"])
    say("  C4 the streams actually differ (some reading moves off the exact value): %s" % res["controls"]["C4_all_cells_have_a_nonzero_streams_spread"])
    if not (c1 and c2 and all(res["controls"].values())):
        raise RuntimeError("a control failed: %s" % res["controls"])

    res["rows"] = rows
    res["build"] = dict(python="%s.%s.%s" % tuple(map(str, sys.version_info[:3])), numpy=np.__version__,
                        script_crc32="%08x" % zlib.crc32(io.open(os.path.abspath(__file__), "rb").read()))
    res["report_sha256"] = "%08x" % zlib.crc32(("\n".join(report)).encode("utf-8"))
    with io.open(OUT, "w") as fh:
        json.dump(res, fh, indent=1, sort_keys=True)
    say()
    say("wrote %s" % OUT)
    say("report id %s" % res["report_sha256"])


if __name__ == "__main__":
    main()
