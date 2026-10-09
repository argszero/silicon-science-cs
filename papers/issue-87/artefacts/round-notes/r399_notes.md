# Issue #87 — R399 notes: the second graph (path), the mechanism's prediction, and a PSD defect the second graph exposed

Scripts: `smoke_v13.py` (the path stratum + the prediction test + the C7 cross-harness control). Comment
`5752817317`. Class 92 in `verification-self-audit-lesson.md`.

## The pre-registered prediction (written before the run, in the script header)

From R398's measured mechanism: `diag(W)` uniform ⇒ axis D is the identity map and axis A's t = 1 endpoint is
`c·I`. Predicted: (P1) on the PATH graph `diag(W)` is measurably non-uniform; (P2) axes A and D then handicap
the rival materially more than on the cycle.

## Results

| read | result |
|---|---|
| P1 diag(W) rel. deviation, worst over 12 bands | cycle 8.2e−16 · complete 4.8e−16 · **path 6.1e−1** (ratio 7.4e14) |
| C7 cycle through this harness vs R398's committed cells | **576/576 exact**, max |Δδ| 0.000e+00, 0 repairs |
| **P2, axis A** | cycle +0.0074 (5/0/19) → path **+0.0059 (8/1/15)** — unchanged ⇒ **REFUTED** |
| **P2, axis D** | cycle −0.0000 (1/1/22, exact zero) → path **+0.0080 (14/0/10)** ⇒ **confirmed in kind, weak in size** |
| axis E (permuted) | +0.0282 (15/1/8) → **+0.0511 (20/1/3)** — nearly doubles |
| axis B (other graph of the pair) | +0.0240 (18/0/6) → +0.0120 (21/0/3) |
| axis C (random PSD metric) | +0.1256 (24/0/0) → +0.1215 (24/0/0) — graph-independent |
| axis F (negative control) | exactly 0 | 
| path stratum, t = 0 delta (quantum − matched) | signs agree with the cycle in **24/24** cells; largest offsets shifted|0.25 +0.096→**+0.024**, unshifted|2 +0.419→**+0.514**; matched rival dominates the middle band on BOTH graphs (up to +0.517 path) |
| determinism (path) | byte-identical rebuild; report sha `49e7659e…` |

## What the half-refutation means (the round's real finding)

Two manipulations that read as the same number — axis A on the cycle (≈ +0.007) and axis D on the cycle
(exactly 0) — have **different causes**:

* D is an **exact structural identity** on a vertex-transitive graph. On the path graph the identity breaks
  and the axis becomes real (14/24), i.e. the symmetry argument is correct and is now confirmed at its own
  boundary.
* A is **absorbed by the tuning protocol**, not by symmetry. Withholding the off-diagonal leaves a DIAGONAL
  metric, i.e. `exp(−s γ² Σ_i d_i (z_i − z′_i)²)` — a coordinate-weighted Hamming kernel whose weights are
  absorbed by the envelope grid that every arm is tuned over (`S_GRID` spans 0.003–10 in the same exponent).
  That is why A stays ≈ 0.006 where the diagonal is non-uniform by 61 %.

**R398's explanation of axis A was therefore incomplete and is corrected here.** The registered power arm is
inert for TWO reasons, only one of which the symmetry argument covers, and the two must be reported
separately: an exact identity (repairable only by changing the graph) and an absorbed family (repairable only
by changing the metric family, which is what axis C does).

## The PSD defect (found by the pre-run probe, not by the long run)

Axis D's mixture leaves the PSD cone on the path graph in **8 of 12 bands** (min eigenvalue down to −6.2, at
γ = 0.1…1.0, shifted): `exp(−s q)` is not a kernel there. The check cannot fire on the cycle, because on the
cycle the axis is a no-op — so R398 could not have seen it. Repair applied and **recorded**: add
`(|λ_min| + 1e−9)·I`, then rescale so `trace` is restored exactly; added amount 0.003–0.198 of the mean
diagonal, scale 0.83–1.00. The repair preserves the axis's named endpoint (C2 for D = 0.000e+00 after
repair). Same defect class as R393's unfloored flag.

## Operational (two defects the probe caught, one of them in the diagnostic itself)

1. `S5.metric_field(...)` called without `gamma` (a copy of R398's `mk_context` lost one positional argument).
2. **The repair log was never written**: `rec` was constructed and dropped — the repair worked (axis D's
   numbers moved) while the counter printed 0. Caught only because the probe PRINTED the count next to the
   changed numbers. Class 92's rule now: a wrapper that claims to log a diagnostic must have its log
   exercised by a probe, not just its effect.
3. The C2 control re-derives axis D at t = 1 through the same wrapper, so a repair record appears twice for
   one matrix; deduped on the identical record (documented in the code).

## Next

q = 8 (a cell where the path/cycle contrast in `diag(W)` is larger), then the calibrated declaration
procedure on axis C's ladder — the fallback clause's power curve in the study's own currency.
