# Issue #87 — R394 notes: a size-VALID null band, its resolution floor, and the power question it raises

R393 built the FDR layer and its size control failed (47–50 % false declarations at a nominal 5 %), with the
cause diagnosed as a **systematic bias**: on a pure-noise target the two arms are not exchangeable, because
the map-fixed kernel shrinks to a nearly constant kernel and that is optimal when there is no signal
(Class 86). This round rebuilt the layer on an empirical null and — the part that matters — **measured the new
layer's own size on an independent null family**, which is what R393 could not do for the old one.

## 1. What was built (`smoke_v8.py`, sha256 recorded in the JSON; 62,785 B result)

- **A calibrated null band** per (convention, bandwidth): 40 independent pure-noise cells, band = the
  2.5/97.5 percentiles of the 40 cell means. The percentiles need no shape assumption, which matters because
  the null is skewed (R393: skew −0.71…−2.36). Resolution 1/(N_CAL+1) = **0.0244 < q_lo = 0.05** — asserted
  in the report, not assumed.
- **The band's own size**, read on a second, independent null family (different seed stream, 20 cells per
  convention): **13 of 240 tests outside the 95 % band = 0.0542, Wilson95 [0.0319, 0.0905]**. The procedure is
  correctly sized. Compare the old one on the SAME nulls: 46.5–48.7 % marginal, and BH declaring 182 (cal)
  + 93 (val) cells.
- **An exchangeability arm.** Note what does *not* work: giving both arms the same kernel makes the paired
  difference identically zero (one fitting function serves both), so it tests nothing. The construction that
  *is* exchangeable randomises the arm each split gets — keep |d|, flip the sign of each paired difference —
  which is exactly the symmetry the sign-flip test and the paired bootstrap assume. Over **40 independent
  randomisations**: sign-flip **0.0493** [0.0393,0.0617], bootstrap **0.0556** [0.0449,0.0686], normal
  **0.0542** [0.0436,0.0671]; BH over the family **0.075** [0.0258,0.1986] (3/40 — small denominator, reported
  as such). **The machinery passes its own assumption.**
- **The degeneracy predicate is now kernel-keyed** — the R393 defect (a threshold on a round-off *mean* let
  3 bogus rows in, m = 39): the key is measured, `max|K_quantum − K_rival| < 1e-12`, and the separation is six
  orders (excluded: 4.4e-16; smallest kept: **7.0e-2**). **m = 36** usable rows, 6 excluded.

## 2. The band is not centred on zero, and that is the R393 bias made visible

| bandwidth | shifted band | unshifted band |
|---|---|---|
| 0.10 | [−0.0501, +0.0301] | [−0.0436, +0.0033] |
| 0.25 | [−0.0359, +0.0452] | [−0.0295, +0.0251] |
| 0.50 | **[−0.0976, −0.0217]** | **[+0.0289, +0.0750]** |
| 1.00 | [−0.0531, +0.0088] | [−0.0796, +0.0013] |
| 2.00 | [+0.0101, +0.0596] | [−0.0010, +0.0538] |
| 3.00 | [+0.0019, +0.0585] | [+0.0111, +0.0651] |

Two of these bands are **entirely on one side of zero** (shifted γ = 0.5 negative, unshifted γ = 0.5
positive), and that is on a target with no signal at all: a zero-effect row can be "significant" against zero
at γ = 0.5 with probability far above 5 %, which is precisely the failure R393 found and this round replaces.
Widths run 0.047–0.081, so the single "±0.06" R393 quoted was a summary of a shape that is neither symmetric
nor homoscedastic.

## 3. The finding this round did NOT expect: the calibrated procedure has a resolution floor, and at m = 36 it is inert

The real grid, read against the band: **27 of 36 rows lie outside their per-cell 95 % no-signal band**
(10 leads, 17 losses) against **1.80** expected by chance. But **BH declares 0** — and the reason is
arithmetic, not the data:

- an empirical p-value from N = 40 null cells has a floor of 2/(N+1) = **0.0488** (26 of our rows sit on it);
- BH at q = 0.05 over m = 36 can only reject if some sorted p satisfies p_(j) ≤ q·j/m, i.e. the smallest
  attainable q is 0.0488 · 36/36 = 0.0488 **only if every row sits on the floor** — one row inside the band
  is enough to lift the minimum q above 0.05 (measured: min q = 0.0676);
- to reach the value BH actually needs at the extreme (p ≈ q/m = 0.0014) the null population would need
  **N ≥ 2/0.0014 − 1 ≈ 1,400 cells per (convention, bandwidth)** — ≈ 35× this round's compute for both
  conventions (~2 h at 2.8 s/cell), and the same wall blocks a family-wise percentile band (a 99.86th
  percentile of 40 values does not exist).

So "0 declared" is a property of the instrument, not evidence about the quantum kernel. **The study's
inferential status is unchanged and unresolved**; what this round establishes is (a) the size fix is real and
validated, and (b) the honest route to a *declaration* is a **smooth null model** (2–3 parameters per
bandwidth) fitted to the empirical null and **validated against it** (KS on the same 40 cells), which reaches
small p-values analytically while keeping the calibration checkable — that is R395's first item.

## 4. What the study can now say

- The old read is **not** repaired by the fix: R393's 28 declarations (12 leads + 16 losses) came from a
  procedure now measured at 46.5–48.7 % false-declaration on pure noise. They are withdrawn as *declarations*
  and remain what they always were — marginal CIs.
- The **descriptive** statement survives: 27/36 rows outside the no-signal band vs 1.8 expected, with the
  large cells (0.39–0.45 of a variance at γ = 0.5–1.0) far outside, and the γ ≤ 0.25 and γ = 3 cells sitting
  at the edge of their own bands (e.g. unshifted γ = 3, α = ±1: −0.0767 / −0.0673 against [+0.0111, +0.0651]).
- No advantage is *declared* anywhere. PB1's middle clause remains NOT OBSERVED (R391), PB3 remains REFUTED
  as written (R392); nothing in this round changes those two, and nothing here upgrades them either.

## 5. Defects and declared deviations of this round

1. **The exchangeability construction had to be argued, not assumed** — the obvious "same kernel for both
   arms" is vacuous here (identical predictions, delta ≡ 0), so the arm randomises the assignment instead.
   Recorded in the module docstring so the next reader does not "fix" it back.
2. **Reduced resampling budget in the comparison arm** (2,000 flips / 1,000 boot vs the 10,000 / 4,000 used
   for the family): route disagreement therefore reads 0.031 rather than v7's 0.006. Declared, not hidden.
3. **Determinism is a spot check, not a full re-run** (one calibration cell re-derived from scratch after the
   report was built: bitwise identical at every bandwidth). A full second report would double a 6-minute run;
   the check is aimed at the dominant cost and says so in the JSON.
4. The calibration family is 40 cells and the validation family 20 per convention — asymmetric on purpose
   (bands are *built* from the larger family, *read* on the independent one), and both numbers are in the
   report.
5. `N_VAL` and the exchangeability count are module constants, so the round is re-runnable at any size — the
   resolution arithmetic in §3 is what fixes them, not convenience.
