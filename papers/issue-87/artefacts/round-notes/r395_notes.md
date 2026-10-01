# Issue #87 — R395 notes: the smooth null, fitted and audited; and what "declared" turns out to mean

R394 ended inert by resolution (`smoke_v8.py`: an empirical p from 40 null draws floors at 0.0488, while BH
at q = 0.05 over m = 36 needs about q/m = 0.0014). The plan was a smooth fitted null per bandwidth. This
round built it — and the round's own controls rejected the first form of it, then rejected the second in a
different way, which is the substance of the result.

## 1. What was built (`smoke_v9.py`, 694 lines, sha `dc56c90d…`, byte-identical over two runs, 45 s)

A **partially pooled** smooth null: the two SHAPE parameters (ε, δ) of a sinh-arcsinh normal are estimated
from the standardised draws of a whole convention (12 bands × 40 = 240 draws), while **location and scale
stay per bandwidth** (median and MAD-based scale of each band's 40 calibration draws). The sinh-arcsinh
family was chosen because its CDF is closed form — p-values need no quadrature and no tail extrapolation by
simulation — and because at δ = 1, ε = 0 it is *exactly* a normal (measured max |ΔF| = 1.1e-16), so the
normal is nested rather than a separate instrument.

Controls that establish the instrument is measuring what it claims:

| control | result |
|---|---|
| R394's committed report recomputes its own sha256 | **matches** (`6c7f5c55…`) |
| one null cell re-derived from scratch vs the stored draws | **identical at all 6 bandwidths** |
| this round's cell runner vs v8's runner, same cell | **bitwise identical at all 6 bandwidths** |
| SHASH at (δ=1, ε=0) vs the normal CDF | max abs diff **1.1e-16** |
| CDF∘PPF round trip | **1.1e-12** |
| density vs numerical dCDF at three points | agree to 9 significant digits |

## 2. The first form of the fix was rejected by the diagnostic: a 4-parameter fit at 40 draws is not identified

The original plan was a 2–4 parameter null *per bandwidth*. Fitting it to 60 synthetic samples of the same
size (40 draws) from a known distribution, **the parameters scatter without bound**: |ε| reaches **59.4**,
δ has mean 3.23 with sd 3.69 (truth 1.40), σ has mean 0.84 with sd 1.24 (truth 1.00). A recovery control on
a 4,000-draw sample had already shown the parameters sit on a very flat ridge — the log-likelihood gap
between the truth and the fitted point was **2.16 in 364,002**, i.e. the surface cannot separate them.

So the plan as stated in R394 was **not implementable**, and the fix is partial pooling: the shape is a
property of the *instrument* under no signal and can be shared across bandwidths; only location and scale are
bandwidth-specific. Pooling moves the shape estimate from 40 to 240 standardised draws.

## 3. The second form passed its size and power checks, and failed its shape audits

| audit | pooled | per-band MLE | normal |
|---|---|---|---|
| size on 240 independent null cells (nominal 5 %) | **3.33 %** [1.70, 6.44] | 4.17 % [2.28, 7.50] | 2.08 % [0.89, 4.78] |
| PIT uniformity of the same 240 cells | **KS 0.1903, p ≈ 0**, mean 0.582 | — | — |
| recovery of a known distribution it was handed | **FAILS**: fitted (ε=−0.077, δ=1.042) vs truth (−0.6, 1.4) | — | — |
| detector power on injected shifts (0.5/1/2/3 σ) | 7.9 / 17.1 / 62.9 / 95.4 % | — | — |
| the registered handicap ladder (t = 0.25/0.5/1) | 16 / 15 / 16 of 18 declared | — | — |

Two things are true at once, and neither may be dropped:

* **The size is conservative** (3.3 % where 5 % is nominal) and **the detector demonstrably fires** — the
  power curve is monotone and the handicap ladder declares at every level, so a large advantage would have
  been found. R394's inertness is fixed: the far tail is now reachable analytically.
* **The fitted null's SHAPE is wrong, asymmetrically.** On the independent null family the PIT fails at
  KS = 0.19 (p ≈ 0), the mean PIT is 0.582, and the **upper** tail is over-populated (5.0 % above 0.95) while
  the **lower** tail is under-populated (2.1 % below 0.05). A conservative overall size therefore does not
  protect every row: the errors are signed. The same conclusion arrives from the synthetic recovery, where
  the pooled shape is pulled toward the normal (ε → −0.08, δ → 1.04).

The honest reading of this table: **the instrument is now usable for large effects and not yet calibrated
for small ones.**

## 4. The real read, and why the count is not the finding

Under the pooled instrument, **27 of 36 rows are declared at q ≤ 0.05** (10 leads, 17 losses); the per-band
MLE gives 29 and the normal fit 29, a heavier-tailed variant gives 18. Only **one** row is declared by the
pooled instrument alone, and **27 are declared by all three** — a stable count. And yet it does not mean
what a count normally means:

* **The smallest declared effect is 0.0059 of a variance** (unshifted, γ = 0.5, α = −1), declared with
  p = 4.4e-15 by the per-band MLE. No reader should believe that a 0.6 %-of-a-variance difference is a
  discovery.
* The reason is visible in R394's own bands: at γ = 0.5 the null's *location* is not zero — the shifted band
  was [−0.0976, −0.0217] and the unshifted [+0.0289, +0.0750], both entirely one-sided. A cell at −0.006 is
  therefore a large deviation **from the no-signal band** and a negligible one **against zero**.
* So "declared" here means *this cell does not behave like a no-signal cell of the same pipeline*. It does
  **not** mean "the quantum kernel beats the matched rival by this much". The two readings answer different
  questions, and the study must say which one it is reporting. The registration asked for the second.

**The defensible core, where both readings agree:** 16 rows with |δ| ≥ 0.053 and p ≈ 0 under all three
instruments and far outside R394's band — **10 losses** at +0.367 … +0.446 (γ = 0.5–2) and **6 leads** at
−0.053 … −0.275 (including the four γ = 3 cells at −0.053 … −0.077). Twelve further rows are declared with
0.006 ≤ |δ| ≤ 0.12 and are instrument-dependent: four of them change status between instruments altogether
(e.g. unshifted γ = 0.5, δ = +0.0127: pooled p = 0.097, per-band p = 1.0e-5, normal p = 0.0100).

## 5. Consequences for the study

* **Nothing is retracted from R391/R392's substance, and nothing is upgraded either.** The large effects are
  the findings; the small ones are instrument-limited.
* **The inferential obstacle now has a name**: the null of the observable is not centred at zero, because the
  two arms shrink differently under no signal (R393's mechanism, measured again in R394's band locations).
  A fitted null makes the *size* right; it does not make the *question* the registration's one. Any
  advantage map from this design is a **relative** map unless the offset is independently removed.
* **R396's first item** is therefore the shape: fit the scale jointly with the shape (the MAD-based scale is
  the prime suspect — it is smaller than the sd in exactly the skewed nulls measured here), re-audit the PIT
  on the same 240 independent cells, and only then re-run the read. Second item: the **path/complete strata**
  and one q = 8 cell, still untouched — every number in every round so far comes from one graph and one seed.

## 6. Defects and declared limits of this round

1. **The first fix was wrong and the diagnostic caught it** — a per-band 4-parameter MLE at 40 draws is not
   identified (parameters scatter to |ε| = 59). Recorded rather than quietly replaced.
2. **The pooled instrument failed its own recovery control.** The round does not claim a calibrated
   small-effect instrument; it claims a conservative one with a measured shape defect.
3. **The 40-draw MLE is retained in the report as an arm**, not deleted — it is the evidence for pooling and
   the source of the most extreme false-small p-value measured here.
4. **One run of ~900 s was CPU contention** from a stale process (the clean run is 45 s); the artifact was
   produced by the clean run and verified byte-identical across two more.
5. The heavier-tailed variant (Student-t base, ν = 5) uses a declared quadrature grid (40 σ, 20,001 points)
   and is a sensitivity arm only.
