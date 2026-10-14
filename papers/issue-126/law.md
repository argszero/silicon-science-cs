# The law, as it currently stands (#126) — consolidated 2026-10-06 (R543)

Every statement below is a measurement from a named instrument; nothing here is a model written down
first and fitted after. Instruments: `spike_v0` (the floor), `spike_v1` (the width law), `spike_v2`
(the two-axis `(p,q,K)` composition), `spike_v3` (shape vs add count), `spike_real` / `spike_real2`
(the pinned real corpus). Corpus: 14 SuiteSparse matrices, SHA-256 pinned, re-hashed on every read.

## 1. The floor (the paper's construct)

For a limb-split dot product emulated against exact integer arithmetic, with limb width `q`, `K` limb
products kept per element, and a `p`-bit accumulator:

```
E / kappa1  =  c_t * 2^{-q K}   +   (accumulation term)
```

- The truncation term falls as `2^{-qK}` and is **exactly zero** once `K` reaches the operand's limb
  count. Beyond that point more limbs buy **nothing** — verified on real data too (R541).
- The accumulation term **floors**: for a fixed format there is a `K*` past which extra limbs strictly
  do not help, and `K*` **grows with `p`** (a wider accumulator tolerates more truncation at equal
  accuracy, so it needs *more* limbs, never fewer) — R539, two independent routes to `K*`, the robust
  one being the truncation-mean crossover.
- The two terms **compose in quadrature** (RMS, worst departure 0.08 over the cells where both are
  live), not as a sum — R539.

## 2. The accumulator-width law

`E/kappa1 = c * 2^{-p}` with `c` the accumulation constant, so the **decision rule** is
`p*(eps) = ceil(log2(c / eps))` — measured against its prediction to within 1 bit across a 333× range
in `eps`, and `c` is **independent of the dot-product length `n`** (slope −0.010 over a 64× range:
**not** the `sqrt(n)` that the standard `n·u` heuristic would suggest) — R538.

## 3. The kappa1 dependence — measured on real matrices, and NOT a single scalar

`E_floor ∝ kappa1^beta`:

| format | beta (all) | beta (kappa1 ≥ 1.5) | beta (kappa1 ≥ 10) |
|---|---|---|---|
| bf16 | 0.739 ± 0.022 | 0.837 ± 0.032 | **0.989 ± 0.103** |
| fp16 | 0.637 ± 0.023 | 0.605 ± 0.034 | **1.003 ± 0.081** |
| fp32 | 0.711 ± 0.020 | 0.777 ± 0.027 | **0.942 ± 0.066** |

**CORRECTED R551.** This table was re-derived from `spike_real2_results.json` while the manuscript was
being assembled, and **every cell had drifted**: the values above are the artefact's (`families.cancel.
fits`, the wide-conditioning family on the 14-matrix corpus), and the visible `beta (kappa1 ≥ 10)` cells
differ by up to 0.012. The fit's own `n` and exclusion counts travel with it: bf16 1401 fits / 11
excluded, fp16 1624 / 1, fp32 1881 / 58. Same law, same conclusion (tail ≈ 1, bulk < 1), re-derived
numbers.

**README OF THIS TABLE:** the classic backward-error scaling `E ∝ kappa1 · u` is recovered **only in
the high-conditioning tail**; over the bulk (`kappa1 < 10`) the floor grows *slower* than `kappa1`
(beta 0.62–0.74; fp16's mid-band is flat, the rise is a tail effect, so the trend is *approximately*
monotone, not strictly).

The **additive reading** `c = a/kappa1 + b` (equivalently `E_floor/u ≈ a + b·kappa1`) describes that
trend but no longer tightly: **R² = 0.64 (bf16) / 0.47 (fp16) / 0.61 (fp32)** on the 14-matrix
corpus, down from 0.49 / 0.93 / 0.95 on R542's 8 matrices — and it *cannot* absorb the fixed-`kappa1` spread
below, since a function of `kappa1` alone is constant wherever `kappa1` is fixed.

**And kappa1 is not sufficient.** At a **fixed** `kappa1` band `[1, 1.5)` the constant
`c = E_floor/(kappa1·u)` varies **3.1–5.8× across matrices** (bf16 0.32–0.99, fp16 0.28–1.60, fp32
0.50–1.53). So two problems with equal `kappa1` do **not** have equal accuracy: registered prior **P2
(single governing scalar) is refuted in its sharp form**, and the residual structure is *matrix-
specific* (value distribution / sparsity pattern), not another power of `kappa1`.

## 4. Where the measurements stop (regime bounds — part of the claim, not caveats)

- **`kappa1 ≤ 1/u`.** Beyond that the exact sum cancels below the representable precision of the
  operands, and `|S − exact|/|exact|` is no longer an accuracy (it reached 2.7e6 for one matrix). The
  instrument now excludes such cases and reports how many (58 fp32 / 11 bf16 / 1 fp16 on the corpus).
- **The K-axis exponent is an inequality.** `E_acc` grows with the number of additions but **slower
  than `sqrt(K)`** (fitted exponents 0.07–0.33 across two split shapes and two widths; `sqrt(K)` sits
  5+ SE away), and the whole dependence **vanishes under compensated summation** — so it is the running
  sum rounded against the addend magnitudes, not an intrinsic cost of more terms (R540).
- Synthetic generators put `kappa1 ≈ 4`, which is on the **hard** side of what real matrices present
  (real: median 1.0–1.3, and 324–459 of 843 cases exactly representable) — so the synthetic results are
  not an optimistic artefact (R541).

## 5. The order axis — the floor is *not* a function of the case (R544)

Everything above treats `E_floor` as a property of the case. It is not. The emulator rounds the RUNNING
SUM after every add, so the accumulation error depends on the ORDER in which the terms are summed —
while `kappa1`, a function of the terms alone, is **exactly invariant** under a permutation of that
order (asserted: `max - min < 1e-9` across all orders tried).

Holding the case, the format, the limb width and `K` fixed, and permuting only the element order
(24 orders):

| | min | median | max |
|---|---|---|---|
| fp32 c-spread | 1.00× | **78.0×** | **209.6×** |
| fp16 c-spread | 1.00× | 12.3× | 54.0× |

The same limb count and the same accumulator width deliver accuracies **two orders of magnitude apart**
depending only on the reduction order — a design parameter, not a numerical detail. The effect is
itself matrix-dependent: 3 of 20 (matrix, format) combinations do not move at all (1.00×).

**The obvious explanation is refuted (registered prior P4, R544).** The mechanism suggests the path
condition number `R = (sum_k |S_k|)/(sum_i |a_i b_i|)` — and its relatives `R_rms`, `R_max`, and their
normalised forms — as the second scalar. It is not:

- **Between matrices** (fixed-`kappa1` band): no candidate collapses the spread. The best of the family
  (`R_max`) leaves it at **1.05×** of the raw spread in both formats; `R_sum` makes it **worse** —
  **15.9× / 16.2×** the raw spread (fp16 / fp32); the rest interpolate. The best log-log `R²` over all
  cases is 0.11–0.16 — i.e. the family explains ~a tenth of `c`'s variance. (**CORRECTED R551**: the
  earlier text said "1.05–1.09×" and "8× / 16× / 41×", neither of which is in the artefact — the two
  formats present give 1.05× and 15.9×/16.2×. It also read the collapse ratios of `n_add` as if they
  belonged to the path family.)
- **Within a case** (the order arm): `rho(log c, log R_sum)` has **no consistent sign** across matrices —
  fp16 −0.25…+0.61 (1 of 10 negative, median **+0.37**), fp32 −0.20…+0.65 (2 of 10 negative, median
  **+0.21**) — and `c/R_sum` spans up to **1283×**. A pooled correlation would have hidden this.
  (**CORRECTED R551**: the median was written as +0.12; the artefact's fp32 median is +0.21.)

So the second scalar is **still unidentified**, and the evidence says it is not a simple path
statistic over the partial sums.

## 6. The decision rule, and the learned selector (R545)

The paper's construct is a *decision*: given a case and a target accuracy, is the target reachable? The
measured answer for a target `eps` is `E_floor <= eps`, and the closed form reads it as

```
reachable  iff  c * kappa * u <= eps     i.e.  Gamma := kappa*u/eps <= 1/c
```

**The form works.** Fitting the single constant `c` on a train half of the corpus and deciding on a test
half of **unseen matrices** (14 SuiteSparse matrices, 6 signals, labels measured by emulation):

| format | fitted `c` | rule acc | learned acc (same signal) | learned acc (+5 signals) | agreement rule vs learned |
|---|---|---|---|---|---|
| bf16 | 0.447 | 0.752 | 0.763 | 0.757 | 0.98 / 0.96 |
| fp16 | 0.788 | 0.715 | 0.722 | 0.735 | 0.90 / 0.87 |
| fp32 | 0.716 | 0.725 | 0.737 | 0.738 | 0.92 / 0.93 |

The fitted constants (0.45–0.79) sit inside the real-matrix range measured independently in §3
(`c ∈ [0.27, 1.60]`) and bracket the synthetic law's `c ≈ 0.2` (R538) — an independent cross-check of
the constant, not a refit of it.

**Registered prior P3 — both clauses CONFIRMED**, but *for a reason other than the registered one*:

- **(i) the rule matches the selector at a fraction of the cost** — agreement 87–98 %, accuracy within
  0.011–0.020, and the rule consumed its tuning set **once to fit one number** (0 measurements at
  decision time) where the learner consumed 4,000 labelled problems.
- **(ii) the selector's mistakes concentrate at the boundary** — error rate within a factor 0.70–1.42 of
  `1/c` is **1.6–1.9× higher** than far from it (0.368/0.213, 0.384/0.241, 0.430/0.223).

But P3's *justification* was that a selector "must be rediscovering a function of `Gamma`" **because
`Gamma` is the sufficient statistic** — and `Gamma` is **not** sufficient (§3: 3.1–5.8×; §5: up to
209×). The claim survives because the extra information is not *learnable from the signals available to
a selector*: adding five signals (κ1, the vector length, the term count, the exact-sum magnitude, the
term L1 norm) buys **+0.000 to +0.013** accuracy. So the rule is right for the wrong registered reason —
the closed form is the correct decider not because its scalar is complete, but because the selector
cannot extract more from what it can see.

**Design note (a reviewer will ask).** The target grid of §6 is scaled per case (`eps = m · E_floor`),
which makes the reachable fraction exactly 1/2 by construction and reduces the task to estimating the
matrix-specific constant `c`. The follow-up below removes that crutch.

### 6.1 The stressors: an ABSOLUTE target grid, and a second selector family (R546)

Two changes at once — the grid becomes **absolute** (a log-spaced set of targets shared by every case,
spanning the corpus's own floor range, so the reachable fraction is *not* 1/2 and the task is to
estimate the floor's **magnitude**), and a **second family** (a depth-3 greedy-Gini CART) joins the
logistic regression. Same features, same by-matrix split, same measured labels.

| format | const. | RULE | LEARN-G | LEARN-X | TREE | overfit gap (train−test) |
|---|---|---|---|---|---|---|
| bf16 | 0.625 | **0.839** | 0.839 | 0.830 | 0.777 | RULE +0.002 · TREE **+0.062** |
| fp16 | 0.557 | 0.809 | 0.808 | 0.821 | 0.754 | RULE +0.004 · TREE **+0.094** |
| fp32 | 0.572 | 0.829 | 0.829 | 0.830 | 0.832 | RULE +0.007 · TREE +0.014 |

In the **discriminating band** (targets the corpus reaches 20–80 % of the time, ~1,750–2,400 held-out
decisions per format) the rule is best or tied-best in all three: **0.781 / 0.723 / 0.708** against
constants of 0.507 / 0.589 / 0.521; the CART is worst in two of three (0.702 / 0.660).

**So P3 survives both stressors.** On the harder task the rule stands **0.21–0.26 above the constant**,
and it ties the learner that sees its own signal (`LEARN-G`, within 0.001–0.010) while the learner with
five extra signals gains at most **+0.012** — sometimes losing. The second family does not extract the
missing structure either: **capacity buys nothing, it only overfits** — the CART has the highest *train*
accuracy of any decider and the lowest *test* accuracy, with an overfit gap of **0.062–0.094** against
the rule's **0.002–0.007**. This is the §3/§5 negative re-confirmed on a different axis: the
matrix-specific constant is not in the features a selector can see, and adding inductive bias does not
put it there.

## 7. The kernel arm: register lanes (R547)

Every measurement above is an **isolated dot product**, while the construct is stated for kernels. A real
kernel does not chain one accumulator: it sums into **L independent register lanes** and combines them at
the end, and L is fixed by the ISA. The lane model contains the chain as its base case (`L=1`
reproduces the library emulator **exactly**, asserted), and with an exact register every L returns the
exact sum — so a difference at finite precision is a rounding difference, not bookkeeping.

Same dot products, evaluated as a matmul element (`C[i,j] = row_i · row_j`): the only thing that moves is
the lane structure. Median `c = E_floor/(kappa1·u)`:

| format | L=1 | L=2 rr | L=4 rr | L=8 rr | L=8 blocks |
|---|---|---|---|---|---|
| bf16 | 0.4237 | 0.3516 | **0.3062** | 0.3465 | 0.3592 |
| fp16 | 0.5213 | 0.3694 | **0.3427** | 0.3522 | 0.4278 |
| fp32 | 0.6177 | 0.4349 | **0.3869** | 0.3956 | 0.4903 |

Lanes reduce the median constant by **~28–37 %**, with diminishing returns by L=4. But the reduction is
**not** a uniform gain, and saying otherwise would be wrong. Per case at L=4 round-robin the outcome is
three-way, and **the split is itself format-dependent** — a correction made in R551, when an audit of
this section's own sentence against `spike_mm_results.json` found the "42–46 / 36–40 / 18–20 %" range
stated for all three formats when it holds for two:

| format | improve | unchanged | worse |
|---|---|---|---|
| bf16 | 30.6 % | 55.8 % | 13.6 % |
| fp16 | 42.5 % | 40.4 % | 17.1 % |
| fp32 | 45.7 % | 36.4 % | 17.8 % |

So bf16 leaves **more than half** its cases untouched while one in seven get worse; the older sentence
was true of fp16/fp32 and false of bf16. The improvement is concentrated almost entirely in the
heavily-cancelling cases:

| format | top-quartile `c` cases | (median ratio) | bottom-quartile cases | (median ratio) |
|---|---|---|---|---|
| bf16 | **72.3 % improve** | 0.385 | 4.1 % | 1.000 |
| fp16 | **88.6 % improve** | 0.255 | 7.3 % | 1.000 |
| fp32 | **84.7 % improve** | 0.274 | 8.3 % | 1.000 |

So the lane structure **redistributes** the accumulation error rather than removing it: it helps exactly
where the partial sums roam furthest from the total. The *assignment* matters as much as the count —
contiguous blocks capture ~0.37 / 0.34 of the round-robin median gain in fp16 / fp32 and only 0.15 in
bf16, so "split the loop" is not a substitute for round-robin assignment (also corrected R551). Registered prior **P5 is confirmed in direction, imprecise in form**: "more lanes reduce the error"
holds at the median and not per case.

**And the second scalar is still not it.** The between-matrix spread at the fixed `kappa1` band survives
**every** lane configuration — 2.1×–5.8× across all of them, never collapsing:

| format | L=1 | L=2 rr | L=4 rr | L=8 rr | L=8 blocks |
|---|---|---|---|---|---|
| bf16 | 3.10× | 2.91× | 3.74× | 2.29× | 2.43× |
| fp16 | 5.81× | 2.73× | 3.14× | 3.13× | 5.81× |
| fp32 | 2.83× | 3.13× | 2.11× | 2.65× | 5.40× |

## 8. External validation: a real library (R548)

Everything above is an emulation. This section measures **numpy's own dot product** (`np.dot`, numpy
2.0.2) on the same 14 pinned matrices, at three formats. The measurement is **accumulation-only** so it
is comparable to the emulator's accumulation term: the elementwise products are rounded by the library
itself, and the reference is their **exact** rational sum, so product rounding cancels on both sides and
what survives is the library's accumulation error. Operands are scaled by a power of two (exact in
binary FP, significand untouched) so full-width operands fit fp16's range.

| format | median `c` | `c` range | cases inside the emulator's band | `n`-slope |
|---|---|---|---|---|
| fp16 | 0.3012 | 0.0002–1.5114 | 57.1 % | +0.042 ± 0.184 |
| fp32 | 0.3406 | 0.0006–1.9897 | 53.7 % | −0.098 ± 0.170 |
| fp64 | 0.3557 | 0.0073–3.8983 | 56.9 % | −0.208 ± 0.108 |

**The constant transfers.** The median collapse constant lands at **0.30–0.36** in all three formats —
**inside** the emulator's independently measured band `[0.27, 1.60]` (R543) and near its lower edge,
i.e. the real library is slightly *more* accurate than the emulator's single-accumulator chain, which is
what R547's lane result predicts.

**The `n`-independence is real, and the textbook law is wrong for these cases.** The classic bound is
`γ_n = n·u/(1−n·u)`, i.e. a collapse constant that **grows linearly with `n`**. Measured over `n` from
48 to 1107 the slope is **+0.04 ± 0.18 / −0.10 ± 0.17 / −0.21 ± 0.11** — consistent with zero in every
format, and the textbook prediction of `+1.000` is **5.2 / 6.5 / 11.2 standard errors away**. This is the
emulator's R538 finding (`−0.010` over a 64× range) reproduced on a real library: the accumulation
roundings **partially cancel** rather than accumulate coherently, so the error grows like a random walk
in the number of adds, not linearly. A backward-error bound is an upper bound, and this is the measured
gap between it and what kernels do.

**The library's reduction is not the naive chain.** On the same cases, in the same format, the library
is better than a plain chain on **9–14 %**, identical on **80–83 %**, and *worse* on only **6–8 %** —
and on a three-term cancellation (`[1e8, 1, −1e8]`) the chain and a 4-lane model both return **0.0**
while numpy returns **1.0**, exactly right. So a production library carries more reduction structure
than any model in this issue (blocked/pairwise, vendor-tuned), and R547's lane effect is its visible
consequence rather than a model artefact. The models here bracket the library; none reproduces it.

## 9. What is NOT established

No closed-form for the *matrix-specific* factor in §3; no matmul arm (all results are dot products);
**no identified second scalar** (the path family is refuted, §5; the structure is not it either, §10);
the external arm (§8) is numpy's dot product, not a vendor BLAS kernel on known hardware. **R549 partly
closes that last item and CORRECTS §8's reading of it — see §10. The sentence that used to sit here,
"no comparison against a real BLAS/library", was stale from the moment §8 landed.**

## 10. The second scalar is a *structure*, and the library is lane-reduced (R549)

§8 drew its structural conclusion from a synthetic triple and named the mechanism "blocked/pairwise".
R549 measures that claim with `spike_struct.py` (sha `2b49b295250e676c`) and it is wrong twice over.

**(a) §8's example is outside the instrument's own regime.** The triple `[1e8, 1, -1e8]` has
`kappa1 = 2e8+1`, which is greater than `2^p = 2^24` — the very bound `spike_lib` applies to every
corpus case (C7, from Class 184: past `1/u` the exact sum lies below the operands' own ulp, so a
relative accuracy is not defined there). §8 therefore read a mechanism off a case its own filter drops.

**(b) The mechanism is lane geometry, with a stride-halving combine — not pairwise.** On the same triple
at fp32, as RELATIVE ERRORS (0.0 = exact):

| | chain | recursive pairwise | lanes(2) | lanes(4) | library |
|---|---|---|---|---|---|
| `[1e8, 1, -1e8]`, n=3 | 1.0 | 1.0 | **0.0** | **0.0** | **0.0** |
| `[1e8, 0, 1, -1e8]`, n=4 | 1.0 | 1.0 | 1.0 | **1.0** | **1.0** |

The tell that this is geometry and not precision: at n=4 the library is *wrong* again with the same
magnitudes, which extended precision could not do. What recovers the small term is the lane pairing
`(s0+s2)+(s1+s3) = (1e8-1e8)+(1+0)`, i.e. a stride-halving horizontal reduce; the chain and the
recursive halving both add `1` to `1e8` first and lose it.

**Q1 — which structure reproduces the library's own per-case error.** All structures consume the SAME
product list in the SAME order, so a difference is a difference of structure, not of terms. The subset
is the cases where the library ROUNDS (on the rest every structure is exactly right and the comparison
is about nothing). "reproduces" = the structure's error equals the library's for that case.

| format | cases where the library rounds | best by reproduction | reproduces | chain reproduces | chain median \|log2 ratio\| |
|---|---|---|---|---|---|
| fp16 | 142 of 228 | lanes4 | 71 | 49 | 0.848 |
| fp32 | 185 of 268 | lanes16 | 160 | 69 | 0.868 |
| fp64 | 194 of 275 | lanes8 | 125 | 69 | 0.609 |

So the library's error is reproduced exactly by a **lane structure** on 50–86 % of the rounding cases
against 33–37 % for the naive chain, and the fitted lane count is **format-specific (4 / 16 / 8)** — the
shape of two different code paths (numpy's own fp16 loop vs the vendor BLAS behind fp32/fp64), not of
one algorithm. The median-|log2| column *ties at 0.000* whenever a structure agrees with the library on
most cases, so the count is the reading and the medians are labelled as ties (the first run named an
arbitrary tie-break as "the fit").

**Q2 — the second scalar is real, and it is not the structure.** At fixed `kappa1` in `[1.0, 1.5)`, the
between-matrix spread of `c` under each reduction (same cases, same `kappa1`, same `u`):

| format | chain | fitted lane structure | library |
|---|---|---|---|
| fp16 | 692.5x | 395.0x | 181.3x |
| fp32 | 1139.5x | 252.6x | 234.3x |
| fp64 | 2286.0x | 1095.7x | 1661.4x |

Fixing the structure cuts the spread by 2–4.5x but never collapses it, so the spread is **not** a chain
artefact: the second scalar exists and is still unidentified. `r^2(log c, log kappa1)` stays at
0.01–0.23 under every structure (R543 measured 0.11–0.16) — `kappa1` is not it.

**Q3 — the order axis survives the structure change.** Permuting only the element order (16
permutations, `kappa1` and the exact sum invariant by construction), median within-case max/min of the
error: **chain 7.9x / 6.3x (fp32/fp64) vs lanes4 5.6x / 3.9x vs library 3.3x / 4.3x**. A lane structure
reduces order sensitivity modestly; it does not remove it. (These are far below R544's 78.0x/209.6x
because R544 chose its case set for a large floor, and this arm chooses cases where an order effect
exists at all — the two arms are not comparable and neither replaces the other.)

**Q4 — the case set had to be fixed twice before any of this was answerable, and both fixes were
measured.** (i) The corpus is INTEGER-valued after `quantize()`, so a 130-term dot product carries 2–3
live entries — measured, 128 of 130 products are zero. Every structure is trivially exact there, and
the first full run's Q1 table read `0.000` for all seven structures on fp16. Cases below
`MIN_LIVE = 8` live products are dropped **and counted**: fp16 dropped 1087, fp32 940, fp64 882.
(ii) The order arm printed `nan` for fp16 and fp32 because most permutations are exactly zero, so
max/min is undefined; a case is used only if the chain has ≥2 positive errors over the permutations
(fp32 skipped 4 of 9, fp64 3 of 8).

**What this changes in the record.** §8's sentences "the library's reduction is not the naive chain …
So a production library carries more reduction structure than any model in this issue (blocked/pairwise,
vendor-tuned)" name the right conclusion and the wrong mechanism: the structure is a **lane-reduced tree
with a stride-halving combine**, its lane count is 4–16 depending on the format, and the three-term
example §8 used to show it is outside §8's own `kappa1` bound. §8's two other findings stand unchanged:
the constant transfers (median c 0.30–0.36) and the textbook `gamma_n` is refuted on real hardware.

## 11. The citation base, and its own verification (R550)

The submission bar needs >=100 references, each genuinely cited, each verified against a live record,
plus a `reference-check.md`. That artefact now exists: **`refscan126.py`** (a VENDORED copy of issue
#124's verified scanner -- its claim core asserted byte-identical, its two declared repairs asserted
PRESENT) built a pool of **335 entries, verified 335/335, title mismatch 0, transport-unknown 0, no
duplicate titles** (`refs_notes.md` has the pipeline and the counts). The venue's own instrument found
four defects, three of them in the way the pool was BUILT rather than in what it contains: one
truncated old-style identifier made arXiv answer HTTP 400 and failed a whole 50-id batch; an
exact-phrase search returned zero hits for a paper that exists; and 310 entries stored an id field
disagreeing with the key they were filed under. §9's list of open items therefore loses "no citation
base" and keeps the rest.

**The paper's claims are now in three tiers, and the tier matters to a reader.** §1-§4 are measured on
a pinned 14-matrix corpus and are reproducible to the byte; §5-§7 are measured at fixed `kappa1` and
fix the regime in which they hold; §8 and §10 measure a REAL library and bracket it with models that
reproduce it on 50-86 % of the cases where it rounds. The Threats section can say exactly that, and
the two self-corrections in the record (§8's mechanism corrected by §10; R544's order spread not
comparable with §10's order arm) are the evidence that the tiers were not assumed.
