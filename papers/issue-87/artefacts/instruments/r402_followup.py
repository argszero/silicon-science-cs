#!/usr/bin/env python3
"""R402 follow-up: repair the mis-specified Q5 comparison, and three descriptive reads the panel permits.

Q5 as PRE-REGISTERED compared the cross-stream sd (the sd of a STREAM MEAN, i.e. of an average over 6 draws)
against R401's `draw_spread_delta` (the sd of a SINGLE draw).  Those are different objects: under iid draws the
stream mean's sd should be close to sigma_draw / sqrt(6) = 0.408 * sigma_draw, so the pre-registered inequality
("stream sd > draw sd") was mis-specified -- the correct contrast is against the 1/sqrt(N_TARGET) benchmark.

This script computes, from the committed panel (smoke_v16_results.json), with no new fitting:

  R1  the corrected unit-of-randomness ratio  r = sd_stream / (sigma_draw / sqrt(6)), per cell and per qubit
      count, against the iid benchmark r = 1.
  R2  finiteness of every number in the panel (a silent NaN would poison a cell's mean).
  R3  the SET of cells where the quantum kernel leads (delta < 0) in each stream -- is the count's stability
      (R402's C5b finding) an identity of cells, or do different cells trade places?
  R4  the q=6 panel mean against R398's committed independent stream: how far apart are two independent
      realisations, cell by cell (the external consistency read).
  R5  the compression read: |delta| at q = 8 over |delta| at q = 6, per cell -- is the q-effect a uniform
      shrinkage toward zero, or is it band-specific?
"""
import io
import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
rep = json.loads(io.open(os.path.join(HERE, "smoke_v16_results.json"), encoding="utf-8").read())
cells = rep["cells"]
keys = sorted(cells)
N_TARGET = rep["n_target"]


def finite(x):
    return isinstance(x, (int, float)) and math.isfinite(x)


print("=" * 100)
print("R402 FOLLOW-UP (post-run; R1 repairs a mis-specified pre-registered comparison)")
print("=" * 100)

# ---- R2 first: nothing below is read off a poisoned cell
bad = []
for k in keys:
    for f, v in cells[k].items():
        if isinstance(v, float) and not math.isfinite(v):
            bad.append((k, f, v))
        if isinstance(v, list) and not all(finite(x) for x in v):
            bad.append((k, f, v))
print("-- R2 finiteness: %d non-finite values in %d cells -> %s"
      % (len(bad), len(keys), "CLEAN" if not bad else bad[:5]))

# ---- R1 the corrected unit-of-randomness comparison
bench = 1.0 / math.sqrt(N_TARGET)
print()
print("-- R1 unit of randomness, corrected: r = sd_stream / (sigma_draw / sqrt(%d)), iid benchmark r = 1 -----"
      % N_TARGET)
rows = []   # no dead scaffolding: the ratio is computed once, below
detail = []
for k in keys:
    for q, sd_key in ((6, "sd6"), (8, "sd8")):
        sd_stream = cells[k][sd_key]
        sig_draw = cells[k]["within_draw_sd_mean"]
        detail.append((k, q, sd_stream, sig_draw, sd_stream / max(sig_draw, 1e-12) / bench))
for q in (6, 8):
    rs = [d[4] for d in detail if d[1] == q]
    print("   q = %d: median r = %.3f  min %.3f  max %.3f  |  r > 1.2 in %d of %d cells  |  r < 0.8 in %d"
          % (q, float(np.median(rs)), min(rs), max(rs), sum(1 for x in rs if x > 1.2), len(rs),
             sum(1 for x in rs if x < 0.8)))
print("   (r ~ 1 means the stream is no more variable than the draws it averages -- the draw spread already")
print("    owns the sampling uncertainty; r >> 1 would mean stream-level variation is missing from it)")

# ---- R3 the lead-cell set
print()
print("-- R3 which cells the quantum kernel leads (delta < 0), per stream ---------------------------------")
for q, dk in ((6, "d6"), (8, "d8")):
    sets = [frozenset(k for k in keys if cells[k][dk][s] < 0) for s in range(len(cells[keys[0]][dk]))]
    same = len(set(sets)) == 1
    print("   q = %d: counts %s  |  identical set across all %d streams: %s"
          % (q, [len(s) for s in sets], len(sets), same))
    if same:
        print("      set: %s" % sorted(sets[0]))
    else:
        union = frozenset().union(*sets)
        inter = frozenset.intersection(*sets)
        print("      stable core %d: %s" % (len(inter), sorted(inter)))
        print("      contested %d: %s" % (len(union - inter), sorted(union - inter)))

# ---- R4 external consistency: the panel vs R398's committed stream
print()
print("-- R4 the q = 6 panel mean vs R398's committed independent stream ----------------------------------")
d = [abs(cells[k]["mean6"] - cells[k]["ref_q6_r398"]) for k in keys]
sd = [cells[k]["sd6"] for k in keys]
print("   |panel mean - R398| : median %.4f  max %.4f  |  over the panel's own sd: median %.2f  max %.2f"
      % (float(np.median(d)), max(d), float(np.median([a / b for a, b in zip(d, sd)])),
         max(a / b for a, b in zip(d, sd))))
worst = max(keys, key=lambda k: abs(cells[k]["mean6"] - cells[k]["ref_q6_r398"]))
print("   worst cell: %s  panel %+.4f +/- %.4f  R398 %+.4f"
      % (worst, cells[worst]["mean6"], cells[worst]["sd6"], cells[worst]["ref_q6_r398"]))
sig = [k for k in keys if abs(cells[k]["mean6"] - cells[k]["ref_q6_r398"]) > 3 * cells[k]["sd6"]]
print("   cells where two independent realisations differ by more than 3 panel-sd: %d %s" % (len(sig), sig))

# ---- R5 compression
print()
print("-- R5 is the q-effect a uniform compression toward zero? -------------------------------------------")
ratios = {k: cells[k]["mean8"] / cells[k]["mean6"] for k in keys if abs(cells[k]["mean6"]) > 1e-9}
big = {k: v for k, v in ratios.items() if abs(cells[k]["mean6"]) >= 0.10}
zmall = {k: v for k, v in ratios.items() if abs(cells[k]["mean6"]) < 0.10}
print("   structure cells (|mean6| >= 0.10, n = %d): ratio q8/q6 -- min %.3f max %.3f mean %.3f"
      % (len(big), min(big.values()), max(big.values()), float(np.mean(list(big.values())))))
for k in sorted(big):
    print("      %-22s %+.4f -> %+.4f   ratio %.3f" % (k, cells[k]["mean6"], cells[k]["mean8"], big[k]))
print("   near-zero cells (|mean6| < 0.10, n = %d): sign flips across q: %d"
      % (len(zmall), sum(1 for k in zmall if np.sign(cells[k]["mean6"]) != np.sign(cells[k]["mean8"]))))
for k in sorted(zmall):
    print("      %-22s %+.4f -> %+.4f   (paired %+.4f, %d/5)"
          % (k, cells[k]["mean6"], cells[k]["mean8"], cells[k]["paired"]["mean"],
             sum(1 for v in cells[k]["paired"]["per_stream"] if v < 0)))

# ---- the resolvable paired effects overall
print()
print("-- R6 how many of the 24 cells have a RESOLVABLE paired q-effect (|mean| >= 3 x sd) ----------------")
res = [k for k in keys if cells[k]["paired"]["resolvable"]]
unan = [k for k in keys if cells[k]["paired"]["unanimity"] == len(cells[k]["paired"]["per_stream"])]
print("   resolvable: %d of 24 | sign-unanimous across streams: %d of 24 | both: %d"
      % (len(res), len(unan), len(set(res) & set(unan))))
print("   non-resolvable cells: %s" % sorted(set(keys) - set(res)))
