# Issue #87 — R398 notes: auditing the registered power arm (the handicap ladder)

Scripts (all re-runnable, byte-identical): `smoke_v12.py` (the audit), `r398_rbf_check.py` (independent
second instrument). Comment `5752484858`. Class 91 in `verification-self-audit-lesson.md`.

## What was in doubt

The registration's risks clause promises a **power arm**: the *planted-alignment ladder*, "a cell where the
metric-matched rival is deliberately handicapped". R393 built it as `W_t = (1−t)W_map + t·diag(W_map)` and read
it under a pipeline whose size control was still failing (47–50%). R393's own table already shows cells where
the "handicapped" rival is far BETTER (t = 0.25, γ = 0.5, δ = +0.384). If withholding geometry improves the
rival, the ladder is not a power arm.

## What was measured

6 axes × 4 levels × 12 bands × 2 planted alignments = 24 cells; each cell = 6 independent (split, noise)
draws × 50 splits; every level is a trace-preserving mixture (pure shape manipulation, envelope's problem
unchanged); t = 0 = the untouched matched metric on every axis.

| axis | valid / reversed / mixed | median dR | range |
|---|---|---|---|
| A registered (off-diagonal withheld) | 5 / 0 / 19 | +0.0074 | [−0.0096, +0.0212] |
| B wrong graph (path) | 18 / 0 / 6 | +0.0240 | [−0.0007, +0.0467] |
| C wrong metric (random PSD) | 24 / 0 / 0 | +0.1256 | [+0.0560, +0.2368] |
| D flat scales | 1 / 1 / 22 | ~0 (1e−13) | [~0, ~0] |
| E permuted (intended positive control) | 15 / 1 / 8 | +0.0282 | [−0.0083, +0.1007] |
| F identity (negative control) | 0 / 0 / 24 | exactly 0 | 0 |

## The mechanism (why axis A is inert) — measured, not inferred

* `diag(W)` is UNIFORM: max relative deviation **8.2e−16** over all 12 bands (cycle graph = vertex-transitive,
  so every qubit has the same scale). Hence axis D is a **no-op by symmetry** (its |dR| ~ 1e−13 = float zero),
  and axis A's t = 1 endpoint is exactly `c·I` ⇒ the rival's kernel is the **isotropic Hamming-RBF family**.
* Second instrument (`r398_rbf_check.py`, same seeds, two kernels, one protocol): R_matched − R_rbf_iso
  mean **−0.0038**, median **−0.0047**, range [−0.0165, +0.0140]; 4 cells all-negative, 0 all-positive;
  144 draws → 91 negative / 53 positive.
* Third route (the study's committed R391 table, α = ±1): R_rbf − R_matched = +0.0046…+0.0258, **12/12
  positive**, median +0.0187 → same SIGN, 4× the magnitude. Reported as an instrument disagreement, not
  smoothed over.

## Consequences recorded

1. The registered axis cannot serve as a graded power curve (premise not established at a usable magnitude).
2. **A valid handicap is named**: axis C, 24/24 valid, median +0.126, and it produces leads (sign changes):
   shifted|0.25 α=+1 +0.0961 → −0.0297; shifted|2 α=+1 +0.0105 → −0.0967; unshifted|0.5 α=+1 −0.0025 →
   −0.1390. Axis B (wrong graph) is the realistic weaker version (18/24, +0.024).
3. **Headline strengthened**: with 100 % of the off-diagonal withheld the rival's dominance is unchanged
   (shifted|0.5 α=+1 δ +0.409 vs +0.421; shifted|1 +0.440 vs +0.448; shifted|0.25 +0.075 vs +0.096).
4. **Methods point for the manuscript**: the "matched" rival and the field's isotropic RBF baseline are within
   ~0.005–0.02 of a variance — the R1-vs-R3 distinction the study draws is not measurable at these settings
   (the randfeat weak-surrogate contrast, δ ≈ +0.40, is unaffected).
5. Axis E as written (permuting the metric's coordinates) is a WEAK positive control — a random metric hurts
   the rival ~4× more than a permutation of the same spectrum does.

## Controls (all pass)

C1 t=0 kernel diff 0.000e+00 on every axis/envelope; C2 each axis at t=1 equals the matrix it names
(0.000e+00 ×5); C3 permutation non-trivial; trace preserved to 1e−9 relative, min eigenvalue > 0 (per band,
per level); C5 negative axis exactly 0 in 24/24; C6 rebuild byte-identical.

Hashes: `a3b8d5d03e0ab26ea28786c52636844306e913204497d13a5b72fa32880d42d1` (smoke_v12 report, = file sha),
`1894a8dfd5327f3c1109dd07f131961c7b97d2cf57f77b763ab399a2cf11061a` (r398_rbf_check report, = file sha).

## Operational

Run cost 12 bands × 2 alphas × 6 draws × 50 splits × 19 kernel-sets ≈ 17 min (double build for C6). stdout was
buffered under `nohup` so progress lines appeared only at the end — use `python3 -u` when the progress matters.
Two arg-slip defects caught by the smoke run before the long run: `k_quantum(..., conv=..., gamma=...)` against
a positional signature, and the first draft's axis-D block (dead code from a copy-paste) — the pre-run single-
band probe is what caught both.
