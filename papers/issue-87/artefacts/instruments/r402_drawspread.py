#!/usr/bin/env python3
"""R402 addendum: measure the DRAW spread at a MATCHED qubit count, so the unit-of-randomness ratio
(sd_stream / (sigma_draw / sqrt(6))) is not built on a denominator that mixes q.

R402's follow-up read that ratio off `within_draw_sd_mean`, which the panel stores AGGREGATED over both qubit
counts (10 realisations: 5 streams x 2 q).  If the draw spread differs between q = 6 and q = 8 -- and it does,
because the kernel and the interaction change -- then r at q = 6 is biased one way and r at q = 8 the other,
and the two numbers cannot be read against each other.  This script re-runs TWO of the panel's five streams at
both qubit counts and persists the per-cell draw spread, so the ratio uses a matched-q denominator.

  * draw_sd(cell, q)  -- sd over the 6 target draws of the per-draw delta (the panel's own construction,
    its own code path: S15.run_map, unchanged);
  * R401's committed q = 8 draw spreads are harvested as an independent third reading at q = 8 (its own
    stream, its own round);
  * r(cell, q) = sd_stream(cell, q) / (sigma_hat_draw(cell, q) / sqrt(N_TARGET)), with sd_stream read from the
    committed panel (smoke_v16_results.json) -- no new fitting for the numerator.

Cost: 2 streams x (q = 6 map + q = 8 map) ~ 11 min.  Deterministic; writes r402_drawspread_results.json.
"""
import io
import json
import math
import os
import sys

import numpy as np

import smoke_v15 as S15
import smoke_v16 as S16

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "r402_drawspread_results.json")
PARTIAL = os.path.join(HERE, "r402_drawspread_partial.json")
PANEL = os.path.join(HERE, "smoke_v16_results.json")
REF_Q8 = os.path.join(HERE, "smoke_v15_results.json")

STREAMS = S16.STREAM_T0[:2]
QUBITS_PAIR = (6, 8)
N_TARGET = S16.N_TARGET


def main():
    print("=" * 100)
    print("R402 ADDENDUM -- the draw spread at a MATCHED qubit count (2 of the 5 panel streams)")
    print("=" * 100)
    panel = json.loads(io.open(PANEL, encoding="utf-8").read())
    ref8 = json.loads(io.open(REF_Q8, encoding="utf-8").read())["rows"]   # the rows, not the whole report:
    assert len(ref8) == 24, len(ref8)                                        # iterating the top level
                                                                             # would have hit the report's
                                                                             # own summary keys (the
                                                                             # KeyError this run died on)
    draw = {}
    for si, t0 in enumerate(STREAMS):
        S15.SEED_T0 = t0
        for q in QUBITS_PAIR:
            rows = S15.run_map(q)
            for k, r in rows.items():
                draw.setdefault(str(q), {}).setdefault(k, {})["stream%d" % si] = float(r["draw_spread_delta"])
            print("   stream %d (SEED_T0 = %d) q = %d: %d cells, mean draw sd %.5f"
                  % (si + 1, t0, q, len(rows),
                     float(np.mean([abs(r["draw_spread_delta"]) for r in rows.values()]))), flush=True)
            # persist INCREMENTALLY: an 11-minute measurement must survive a later crash (this script lost one
            # such measurement to a KeyError raised after the fits were already paid for)
            io.open(PARTIAL, "w", encoding="utf-8").write(json.dumps(
                dict(round="R402-addendum-partial", streams=list(STREAMS), n_target=N_TARGET,
                     draw_spreads=draw), indent=1, sort_keys=True, default=float))

    # harvest R401's committed q = 8 draw spreads (an independent third reading)
    for k, row in ref8.items():
        draw["8"][k]["r401_committed"] = float(row["draw_spread_delta"])
    print("   harvested R401's committed q = 8 draw spreads (%d cells)" % len(ref8))

    # the ratio, corrected
    bench = 1.0 / math.sqrt(N_TARGET)
    out = {}
    for q in QUBITS_PAIR:
        qs = str(q)
        ratios, sigmas = {}, {}
        for k in sorted(draw[qs]):
            sd_draw = float(np.mean([abs(v) for v in draw[qs][k].values()]))
            sigmas[k] = sd_draw
            sd_stream = panel["cells"][k]["sd6" if q == 6 else "sd8"]
            ratios[k] = sd_stream / max(sd_draw, 1e-12) / bench
        out[qs] = dict(sigma_draw_mean=float(np.mean(list(sigmas.values()))),
                       sigma_draw={k: v for k, v in sigmas.items()},
                       ratio={k: v for k, v in ratios.items()},
                       ratio_median=float(np.median(list(ratios.values()))),
                       ratio_min=float(min(ratios.values())), ratio_max=float(max(ratios.values())),
                       n_above_1p2=int(sum(1 for v in ratios.values() if v > 1.2)),
                       n_below_0p8=int(sum(1 for v in ratios.values() if v < 0.8)))
        print()
        print("-- q = %d: mean draw sd %.5f (over %d cells x %d readings) | ratio r = sd_stream / (sd_draw / "
              "sqrt(%d))" % (q, out[qs]["sigma_draw_mean"], len(sigmas), len(draw[qs][sorted(draw[qs])[0]]),
                             N_TARGET))
        print("   median %.3f  min %.3f  max %.3f  |  r > 1.2 in %d of %d  |  r < 0.8 in %d"
              % (out[qs]["ratio_median"], out[qs]["ratio_min"], out[qs]["ratio_max"],
                 out[qs]["n_above_1p2"], len(ratios), out[qs]["n_below_0p8"]))

    rep = dict(round="R402-addendum", streams=list(STREAMS), n_target=N_TARGET, bench=bench,
               draw_spreads=draw, ratio=out,
               note="numerator = the committed panel's cross-stream sd per cell; denominator = the mean of the "
                    "per-cell draw spreads measured on %d streams (q = 8 also carries R401's committed stream)"
                    % len(STREAMS))
    io.open(OUT, "w", encoding="utf-8").write(json.dumps(rep, indent=1, sort_keys=True, default=float))
    print()
    print("   written to %s" % os.path.basename(OUT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
