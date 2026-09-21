#!/usr/bin/env python3
"""R402 pre-flight: the wiring probe the R399/R401 lessons demand before a long run.

1. one band at q = 6 and one at q = 8 through the panel's own call path (S15.run_map) -- catches a name or
   shape error in seconds instead of 45 minutes in;
2. C2 in full: rerun R401's committed stream on one q = 8 band and compare to the committed rows;
3. the per-cell statistics on the two probe bands, so the aggregation code is exercised too.
"""
import sys
import time

sys.path.insert(0, "/Users/argszero/scm/github.com/argszero/silicon-science-cs/papers/issue-87/research")

import numpy as np
import smoke_v15 as S15
import smoke_v16 as S16

BAND = [("shifted", 1.0)]
t0 = time.perf_counter()
S15.SEED_T0 = S16.STREAM_T0[0]
r6 = S15.run_map(6, only=BAND)
print("q=6 probe band ok in %.1fs: %s" % (time.perf_counter() - t0, sorted(r6)))
print("   sample:", {k: round(v, 6) for k, v in sorted(r6.items())[0][1].items()
                     if isinstance(v, float)})

t0 = time.perf_counter()
S15.SEED_T0 = S16.R401_T0
r8 = S15.run_map(8, only=BAND)
ref8 = S16.harvest_q8()
worst, n, mis = 0.0, 0, 0
for k, row in sorted(r8.items()):
    for f in ("r_quantum", "r_matched", "delta_vs_matched", "r_matched_random_metric"):
        a, b = ref8[k][f], row[f]
        worst = max(worst, abs(a - b))
        n += 1
        mis += int(a != b)
print("C2 committed reproduction: identical=%s (%d values, max |diff| %.3e, mismatches %d) in %.1fs"
      % (mis == 0, n, worst, mis, time.perf_counter() - t0))

# aggregation path on a synthetic panel of the two probe cells
for k in sorted(r6):
    d6 = [r6[k]["delta_vs_matched"] + 0.001 * i for i in range(5)]
    d8 = [r8[k]["delta_vs_matched"] + 0.002 * i for i in range(5)]
    p = S16.paired_effect(d6, d8)
    u, s = S16.uniformity(d6)
    print("   %-22s unanimity=%d/%d paired mean %+.4f sd %.4f resolvable=%s"
          % (k, u, len(d6), p["mean"], p["sd"], p["resolvable"]))
print("PRE-FLIGHT OK")
