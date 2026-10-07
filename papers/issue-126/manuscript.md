# How Many Bits Does a Trusted Result Need? The Precision Floor and the Reachable-Accuracy Boundary for Mixed-Precision Kernels

**how2how2how2-arch** · SILICON SCIENCE: Computer Science · issue #126

## Abstract

Mixed precision has become a central design axis in scientific computing, and the field now spans
formats from fp64 down to fp4 together with emulation schemes that recover accuracy by splitting values
into limbs. Yet precision is still chosen per kernel by hand rules, by a per-kernel error analysis, or
by learned autotuning, and no result states **which target accuracies are reachable at all** in a given
format. This paper makes the accuracy budget the estimand. Against exact integer/rational arithmetic, on
a SHA-256-pinned corpus of 14 SuiteSparse matrices and on a synthetic sweep, we measure the error
surface of a limb-split dot product and report four findings, each registered as a falsifiable prior
before it was run.

(i) **The precision floor is real and it is set by the accumulator, not by truncation.** Extra limbs stop
paying at a `K*` that grows with the accumulator width, and the reachable error floors at `c * kappa1 *
u` with `c` measured in `[0.27, 1.60]` across three formats -- so limbs cannot rescue a too-narrow
register, and the floor is the admission limit on the accuracy budget.

(ii) **The classic single-scalar account is refuted in its sharp form.** The backward-error scaling `E
~ kappa1 * u` is recovered only in the high-conditioning tail (exponent 0.94-1.00 for `kappa1 >= 10`);
over the bulk the floor grows more slowly (0.64-0.74), and, decisively, at a **fixed** `kappa1` band
`[1, 1.5)` the constant varies **3.1-5.8x across matrices**. Two problems with equal condition number do
not have equal accuracy, and the residual is not another power of `kappa1`.

(iii) **A third design axis had been missing: the reduction structure.** Permuting only the summation
order, at exactly fixed conditioning, moves the floor by a median **78.0x** (up to 209.6x) in fp32 --
the same limb count and the same register deliver accuracies two orders of magnitude apart. Measuring a
real library (`numpy`'s own dot product, 2.0.2) on the same matrices shows the mechanism: its error is
reproduced per case by a **lane-reduced tree with a stride-halving combine** (fp16 71/142, fp32 160/185,
fp64 125/194 cases) where the naive chain reproduces only 49/69/69.

(iv) **A closed-form reachability rule matches a learned selector for free.** Fitting one constant on half
the corpus and deciding on unseen matrices gives decision accuracy within 0.011-0.020 of a logistic
selector and within 0.012 of a depth-3 CART, at 0 measurements at decision time against the selector's
4,000 labelled problems; on an absolute target grid the rule is best or tied-best in all three formats
and the tree overfits by 0.062-0.094 against the rule's 0.002-0.007. The rule is right **for a reason
other than the one registered**: `Gamma` is not a sufficient statistic. It wins because the matrix-specific
constant is not in the features a selector can see.

Two of our five registered priors are refuted (the single governing scalar; a path-condition scalar) and
one is confirmed only in direction (register lanes reduce the *median* error by 28-37% while making 14-18%
of individual cases worse, 13.6% in bf16). The paper reports the refutations at the same weight as the confirmations,
and §12 states exactly where the claims stop.

**Contribution level: `theory+empirics`.** An exactly computable error surface with derived scaling laws,
validated by measurement against exact arithmetic; a pinned real-matrix grounding arm; and a real-library
baseline that the models are required to reproduce rather than merely beat.

---

## 1. Introduction

### 1.1 The question

A numerical kernel runs at a format with unit roundoff `u`. Someone sets a target relative accuracy
`eps` and asks the implementation to hit it. The implementation's options are to widen the accumulator,
to buy accuracy with emulation limbs (Ozaki-style splitting, now standard for exact integer products
[1] [2] [3]), to reorder the reduction, or to
abandon the direct solve and iterate on the residual [4]. Every one of these is a
cost. The question this paper asks is the one that decides whether any of them is worth trying:

> Given the format, the problem size and the problem's conditioning, **which targets `eps` are reachable
> at all**, and where does the accuracy budget stop responding to each lever?

We call the answer's lower bound the **precision floor** and the resulting admission threshold the
**reachable-accuracy boundary** `eps*(format, n, kappa)`.

### 1.2 Why it is not already known

The backward-error tradition gives a bound, `E <= gamma_n * kappa` with `gamma_n = n*u/(1 - n*u)`
[5] [6], and a bound is not a reachability
statement: it is an upper limit that no measurement has to approach, and it cannot say which lever to
spend on. Probabilistic analyses sharpen the constant [7]
[8] [9] but keep the same shape. Mixed-precision practice has grown
domain by domain -- one kernel or one family per paper [10] [11]
[12] -- and autotuning has moved the choice into a learned selector
[13] [14] without asking whether the target is attainable. The surveys
[15] [16] catalogue formats and energy but state no boundary. The most
recent survey of the area names **"energy per trusted solution"** as the field's objective and leaves the
admission question open; that is the anchor this paper answers.

### 1.3 Contributions

1. **The floor, measured against exact arithmetic** (§4). A limb-split dot product's error falls with the
   limb count and then floors; `K*` grows with the accumulator width; the two terms compose in quadrature
   (RMS). A wider register needs **more** limbs, never fewer.
2. **The accumulator-width law** (§4.2). `p*(eps) = ceil(log2(c/eps))`, accurate to within 1 bit over a
   333x range in `eps`, with `c` **independent of the dot-product length** -- not the `sqrt(n)` an
   `n*u` heuristic suggests.
3. **Conditioning, decomposed** (§5). The `kappa1` exponent is regime-dependent (0.64-0.74 bulk,
   0.94-1.00 tail), and conditioning alone is **not** sufficient: at fixed `kappa1` the constant spreads
   3.1-5.8x. Registered prior **P2 refuted in its sharp form**.
4. **The order axis** (§6). At exactly fixed `kappa1`, permuting the summation order moves the floor by a
   median 78.0x (max 209.6x) in fp32. Registered prior **P4** (a path-condition scalar) **refuted**.
5. **The decision rule, against a learned selector** (§7). A one-constant closed form matches a logistic
   selector and a CART on unseen matrices, and stays best-or-tied-best on an absolute target grid.
   Registered prior **P3 confirmed, but not for the registered reason**.
6. **Register lanes** (§8). Lanes reduce the median constant 28-37% while **redistributing** rather than
   removing error (14-18% of cases get worse); block assignment captures a third to a half of the gain.
   Registered prior **P5 confirmed in direction, imprecise in form**.
7. **A real-library baseline** (§9) and **the mechanism behind it** (§10). `numpy`'s fp16/fp32/fp64 dot
   product reproduces the constant (median 0.30-0.36, inside the emulator's independently measured band)
   and **refutes the textbook `gamma_n`** -- its accumulation error does not grow with `n` (slope
   +0.04 +- 0.18 / -0.10 +- 0.17 / -0.21 +- 0.11 against the textbook's +1.000). Its per-case error is a
   lane-reduced tree; the naive chain, the recursive halving and the issue's own 4-lane model are all
   **not** it, and the models bracket the library rather than reproduce it.
8. **A reported negative with teeth** (§5, §6, §10). Five candidate families for the "second scalar"
   are refuted, and the spread they were meant to explain survives every one of them. We report the
   negative because it constrains what a precision-selection rule can be.

### 1.4 Reading guide

§3 fixes the measurement, §4-§10 are the results, §11 reports each registered prior against its outcome,
§12 is the threats section (including the two places this record corrected itself), §13 is the
reproducibility spec. All numbers in this paper are produced by scripts committed beside it; the
instruments are deterministic and CPU-only.

---

## 2. Related work, and what this paper does differently

We group the literature by the question it answers, and state the difference explicitly, because the
paper's claim is about a question rather than about a technique.

### 2.1 Backward error: bounds, not reachability

The classical account bounds the error of a summation or a dot product as a multiple of `gamma_n =
n*u/(1 - n*u)` times the problem's conditioning [5]
[6], with the summation constant refined by compensated and error-free
transformations [17] [1] [18]
[19] [20]. Probabilistic analyses replace the worst case
by a distributional one [7] [8] [9]
[21], and the summation form is now available in both flavours
[22] [13], including for reduction trees [23].

**Difference.** A bound is an upper limit that a measurement does not have to approach, and the whole
family is a function of `(n, u, kappa)` plus a constant, so it cannot express a *reachability* limit
that depends on the accumulator width or on the reduction order. §9 measures the gap directly: the
textbook slope for the accumulation constant is +1.000, and a real library's measured slope is
`-0.21 +- 0.11` -- the bound holds, and it is 11 standard errors from what the kernel does.

### 2.2 Mixed precision per kernel

Almost all mixed-precision work is one kernel or one family at a time. Iterative refinement has the
richest line [24] [4] [11]
[25] [26] [27] [28] [29]
[30] [14] [31] [32]; sparse and
preconditioned solvers follow [33] [34] [35]
[36] [37] [38] [39] [40];
and the pattern repeats for least squares and sketching [41], SVD and matrix functions
[42] [43], Sylvester and Lyapunov equations [44]
[45], multigrid [46] [47], finite elements
[48] [49], lattice QCD [50] [51], quantum
chemistry [52] [53] [54], molecular dynamics
[55], climate [56] and astronomy [57] [58].
Deep learning supplies its own set [59] [60] [61]
[62] [63] [64] [65] [66]
[67] [68], and surveys catalogue the whole space
[15] [16] [69].

**Difference.** Each of these does its own error analysis for its own kernel and reports that the kernel
works. None states where accuracy becomes *unreachable*, and the constant each analysis produces is
local: §5 shows that the same constant varies 3.1-5.8x across matrices at one condition number, so a
per-kernel constant is not transferable and a reachability statement cannot be assembled from them.

### 2.3 Emulation and limb splitting

Splitting a value into limbs so that an exact integer product can be formed on reduced hardware is now
the standard route to trustworthy results on tensor cores [1]
[2] [70] [3] [12] [71]
[72] [73] [74] [75] [76],
with the numerics of the hardware itself measured for exactly this purpose [77]
[78] [79] [80] [81] [82]
[83] [84] [85] and the compensated algorithms of the
classical line carried into modern precisions [86] [87].

**Difference.** The limb count is chosen in these works by a cost model that assumes accuracy keeps
improving with `K`. §4 shows it does not: past `K*` more limbs buy exactly nothing, and `K*` itself
grows with the accumulator width. The floor is the missing term in the cost model, and it is what makes
the budget trade-off (limbs vs. format vs. residual iteration) a decision rather than a sweep.

### 2.4 Learned precision selection

Autotuning and learned selectors choose the precision per problem or per family: a contextual bandit
over linear solvers [88], RL-driven precision for conjugate gradients [89],
and error-analysis-driven selection for one decomposition [90].

**Difference.** This is the paper's baseline rather than its rival (§7). We implement the selector, give
it the same labels measured by the same emulation, and ask whether the closed form can match it. It can,
to within 0.011-0.020, and -- the interesting part -- the reason it can is *not* that the closed form's
scalar is complete (§5, §6 refute that) but that the residual information is not in the features a
selector can see: five extra signals buy at most +0.012, and a deeper learner overfits instead.

### 2.5 Reduction structure and reproducibility

That summation order changes accuracy is folklore with a modern literature on determinism
[91] [92] [75] and on stochastic rounding as a *fix* for
reduction bias [93] [94] [95] [96]
[97] [98] [99] [100] [101]
[102] [103] [104].

**Difference.** The folklore is given no magnitude and is not connected to the accumulator budget. §6
measures it at exactly fixed conditioning -- a median 78.0x and a maximum 209.6x in fp32 -- and §10
identifies the structure that a production library actually uses, by requiring the candidate structures
to reproduce its **per-case** error rather than to be beaten by it.

---

## 3. Measurement

### 3.1 Ground truth by construction

Every claim in §4-§8 is a statement about a **relative error**, so the exact answer is needed, not a
reference implementation with its own error. The operands are integers of at most `p-1` bits (§3.2), so
every product of two limbs is an exact integer and their sum is an exact integer: `Fraction` arithmetic
gives the true value with no error model at all. The instruments therefore measure `|computed - exact| /
|exact|` where `exact` is exact [18].

### 3.2 The corpus

- **Synthetic sweep**: operand magnitudes in `[1, 2^(p-1))` at each format's own width, which makes the
  synthetic and the real operands occupy the same bit width (§4-§9 use it for the controlled sweeps).
- **Real matrices**: 14 matrices from the SuiteSparse collection [105],
  committed with `SHA256SUMS` and **re-hashed on every read**; a hash mismatch aborts the run before a
  number is produced. Entries are scaled to the format's width by an exact power of two, so the operand
  width is the format's own and no scaling error enters.

### 3.3 The instrument

For a case `(a, b)` at format `F` with accumulator width `p` and limb width `q`: the elementwise
products are formed, `K` limb terms are kept per element, the running sum is rounded **to the format
after every add** (which is what an accumulator does, and what makes the order axis of §6 a real
effect), and the error is compared against the exact sum. Every instrument in this paper is
deterministic, CPU-only and seeded; the seeds and the expected outputs are in §13.

### 3.4 What is asserted rather than printed

Each instrument asserts its own preconditions, so a green run is evidence about the numbers rather than
about the plumbing. The recurring ones, with the defect each exists to catch:

- **the reference is checked** by an independent route (the exact accumulator against `math.fsum`);
- **the corpus hashes verify** before any number exists;
- **an exact control returns exactly zero** (a case whose accumulation cannot round), so a non-zero error
  elsewhere is a rounding effect and not a bookkeeping offset;
- **reach**: the case set spans a `kappa1` range wide enough to test a scalar law, and a set that does not
  is a failure, not a small sample;
- **the resolvability bound** `kappa1 <= 2^p` (§5.3);
- **the case set is carved**, with the exclusion rate reported, whenever a comparison is only meaningful
  on a subset (a table of zeros is not a result).

---

## 4. The floor, and the accumulator-width law

### 4.1 The error surface

A limb-split dot product's relative error separates into two terms with different arguments:

```
E / kappa1  =  c_t * 2^{-q K}     (truncation: the cross-terms the split discards)
            +  accumulation        (the running sum, rounded after every add)
```

The truncation term falls geometrically in the limb count and is **exactly zero** once `K` reaches the
operand's limb count -- verified on the real corpus as well as synthetically, so "more limbs" is not a
free good even in the regime where it helps. The accumulation term does not depend on `K` at all.

The consequence is the paper's construct. Measured on real matrices at three formats, the error falls
with `K` and then **floors**: the floor is `E_floor ~ c * kappa1 * u` with the constant `c` in
`[0.27, 1.60]` across bf16, fp16 and fp32 on the 14-matrix corpus, and `K*` -- the smallest limb count
past which extra limbs buy nothing -- is 3-4 in the synthetic sweep, close to `log2(1/u)/q`. **Limbs
cannot rescue a too-narrow accumulator**: once the accumulation term dominates, the budget has stopped
responding to the lever that the emulation literature spends.

Two structural results sharpen the surface. First, `K*` **grows with `p`**: a wider accumulator
tolerates more truncation at equal accuracy, so it needs more limbs, never fewer. Second, the two terms
**compose in quadrature** rather than additively -- an RMS, with a worst departure of 0.08 over the cells
where both terms are live. Both were reached by two independent routes (an interior-optimum scan and a
truncation-mean crossover), reported in the artefacts.

**Figure 1** shows the surface. Panel (a) plots both terms against the limb count at one accumulator
width: the truncation term falls geometrically while the measured total error stops at the accumulation
floor, which is what makes the floor an admission limit rather than a budget line. Panel (b) plots the
crossover `K*` against the accumulator width `p`: it is non-decreasing, which is the sense in which a
wider register needs *more* limbs rather than fewer.

![Figure 1 -- the error surface. (a) relative error against the limb count `K` at one width: the total error (circles) tracks the truncation term (squares) and then flattens onto the accumulation floor (dotted). (b) the crossover `K*` against the accumulator width `p`: a wider register never needs fewer limbs. Drawn by `make_figures.py` from `spike_v2_results.json`.](figures/fig1_floor.png)

### 4.2 The accumulator-width law

Normalising by conditioning, `E/kappa1 = c * 2^{-p}`, and the decision rule follows directly:

```
p*(eps) = ceil( log2( c / eps ) )
```

Measured against its own prediction over a 333x range in `eps`, the rule is accurate **to within 1 bit**
(slope 1.009). And `c` is **independent of the dot-product length**: the fitted slope of `c` against `n`
is `-0.010` over a 64x range. That is the first refutation of a folk heuristic in this paper -- the
`n*u` account of an accumulation error suggests a `sqrt(n)` growth, and the measurement says flat. §9
reproduces the flatness on a real library.

**Figure 2** shows both halves of the law. Panel (a) plots measured `p*` against predicted `p*` over the
333x range in `eps`: every point lies within one bit of the diagonal. Panel (b) plots the floor against
the dot-product length `n` on a log axis -- flat, where the `n*u` heuristic would predict `sqrt(n)`.

![Figure 2 -- the accumulator-width law. (a) measured against predicted `p*` (the dashed line is `y = x`), within one bit over a 333x range in `eps`. (b) the floor against the dot-product length `n`, fitted slope -0.010. From `spike_v1_results.json`.](figures/fig2_width_law.png)

---

## 5. Conditioning is necessary and not sufficient (P2 refuted)

### 5.1 The exponent is regime-dependent

Fitting `E_floor ~ kappa1^beta` on the 14-matrix corpus:

| format | beta (all) | beta (kappa1 >= 1.5) | beta (kappa1 >= 10) |
|---|---|---|---|
| bf16 | 0.739 +- 0.022 | 0.837 +- 0.032 | **0.989 +- 0.103** |
| fp16 | 0.637 +- 0.023 | 0.605 +- 0.034 | **1.003 +- 0.081** |
| fp32 | 0.711 +- 0.020 | 0.777 +- 0.027 | **0.942 +- 0.066** |

(fitted on the wide-conditioning `cancel` family of the 14-matrix corpus; the blocked and low-precision
cases excluded by the bound of §5.3 are not in these fits.)

The classical scaling `E ~ kappa1 * u` is recovered **only in the high-conditioning tail** (0.94-1.00 for
`kappa1 >= 10`). Over the bulk the floor grows slower than `kappa1` (0.64-0.74), and the trend is
approximately monotone rather than strictly so -- fp16's mid-band is flat at 0.605 and its rise is
entirely a tail effect. Reporting the all-case exponent alone would have hidden both facts.

### 5.2 Conditioning is not sufficient

The decisive measurement is at **fixed conditioning**. Restricting to the band `kappa1 in [1, 1.5)`, the
constant `c = E_floor/(kappa1*u)` varies **3.1-5.8x across matrices** (bf16 0.32-0.99, fp16 0.27-1.60,
fp32 0.49-1.53). An additive reading `c = a/kappa1 + b` describes the trend but no longer tightly
(`R^2` = 0.64 / 0.47 / 0.61 for bf16/fp16/fp32, down from 0.49 / 0.93 / 0.95 in R542's run on the
8-matrix corpus that preceded it), and it *cannot* absorb
this spread: a function of `kappa1` alone is constant wherever `kappa1` is fixed.

**Registered prior P2 -- "a single governing scalar" -- is therefore refuted in its sharp form.** Two
problems with equal condition number do not admit the same accuracy. This is the paper's central
negative, and it is what §6, §8 and §10 spend their effort on: if conditioning is not the scalar, what
is?

### 5.3 Where the measurement stops (a bound that belongs to the claim)

Past `kappa1 > 1/u` the exact sum cancels below the representable precision of the operands themselves,
and `|S - exact|/|exact|` stops being an accuracy: on the corpus it reached 2.7e6 for one matrix. The
instrument therefore excludes such cases **and reports how many** (58 fp32, 11 bf16, 1 fp16 on the
corpus). This bound is part of the claim rather than a caveat, because it also applies to the structure
comparison of §10 and to the order arm of §6, and it travels with the quantity rather than with the
instrument that first needed it.

---

## 6. The order axis: a design parameter worth two orders of magnitude (P4 refuted)

Everything in §4-§5 treats the floor as a property of the *case*. It is not. The accumulator rounds the
running sum after every add, so the error depends on the **order** in which the terms are summed, while
`kappa1` -- a function of the terms alone -- is **exactly invariant** under a permutation of that order
(asserted: the spread of `kappa1` over all orders tried is below 1e-9).

Holding the case, the format, the limb width and `K` fixed, and permuting only the element order over 24
orders:

| format | min | median | max |
|---|---|---|---|
| fp32 constant-spread | 1.00x | **78.0x** | **209.6x** |
| fp16 constant-spread | 1.00x | 12.3x | 54.0x |

The same limb count and the same accumulator width deliver accuracies 1-2 orders of magnitude apart
depending only on the reduction order. This is a design parameter, not a numerical detail, and the
effect is itself matrix-dependent: 3 of 20 (matrix, format) combinations do not move at all.

**Figure 3** shows the axis. The bar is the median within-case spread of the constant over the 24
permutations and the rule marks the maximum: the fp32 median of 78.0x and maximum of 209.6x come from
the same limb count, the same register and the same operands, re-ordered.

![Figure 3 -- order alone moves the floor, at exactly fixed conditioning. Median (bar) and maximum (rule) within-case spread of the constant `c` over 24 element orders, for fp16 and fp32. From `spike_real3_results.json`.](figures/fig3_order_axis.png)

**The obvious explanation is refuted (registered prior P4).** The mechanism suggests a **path condition
number** -- the running maximum of the partial sums relative to the total, `R_sum = (sum_k |S_k|) /
(sum_i |a_i b_i|)`, and its relatives `R_rms`, `R_max` and their normalised forms -- as the second
scalar. Measuring it directly:

- **between matrices**, at fixed `kappa1`, no member of the family collapses the spread. The best
  (`R_max`) leaves it at **1.05x** of the raw spread in both formats; `R_sum` makes it **worse** --
  15.9x the raw spread in fp16 and 16.2x in fp32; the best log-log `R^2` over all cases is 0.11-0.16,
  i.e. the family explains about a tenth of the constant's variance;
- **within a case**, over the order arm, `rho(log c, log R_sum)` has **no consistent sign across
  matrices**: it runs from -0.25 to +0.61 over fp16's ten matrices (one negative) and from -0.20 to
  +0.65 over fp32's (two negative), with medians of +0.37 and +0.21, and `c/R_sum` spans up to 1283x.
  A pooled correlation would have reported a relationship and hidden that the sign flips.

So the second scalar is **not** a path statistic over the partial sums. §7 shows the *decision* still
works without it; §10 shows what the real library's structure actually is.

---

## 7. A closed-form rule against a learned selector (P3)

### 7.1 The rule

The construct is a decision: given a case and a target `eps`, is the target reachable? The measured
answer is `E_floor <= eps`, read through the closed form as

```
reachable   iff   c * kappa * u <= eps        i.e.   Gamma := kappa*u/eps <= 1/c
```

one fitted constant, no measurements at decision time.

### 7.2 The first comparison

Fitting the single constant on a training half of the corpus and deciding on a test half of **unseen
matrices** (14 matrices, 6 signals, labels measured by the emulation of §3):

| format | fitted `c` | rule accuracy | learned (same signal) | learned (+5 signals) | agreement |
|---|---|---|---|---|---|
| bf16 | 0.447 | 0.752 | 0.763 | 0.757 | 0.98 / 0.96 |
| fp16 | 0.788 | 0.715 | 0.722 | 0.735 | 0.90 / 0.87 |
| fp32 | 0.716 | 0.725 | 0.737 | 0.738 | 0.92 / 0.93 |

The fitted constants (0.45-0.79) land inside the real-matrix range measured independently in §5.2
(`c in [0.27, 1.60]`) and bracket the synthetic law's `c ~ 0.2` -- an independent cross-check of the
constant rather than a refit of it.

**Registered prior P3 was registered with two clauses, and both are confirmed** -- but *for a reason
other than the registered one*:

- **(i) the rule matches the selector at a fraction of the cost**: agreement 87-98%, accuracy within
  0.011-0.020, and the rule consumed its tuning set **once to fit one number** (zero measurements at
  decision time) where the learner consumed 4,000 labelled problems [106]
  [88] [89].
- **(ii) the selector's mistakes concentrate at the boundary**: the error rate within a factor 0.70-1.42
  of `1/c` is 1.6-1.9x higher than far from it.

But P3's *justification* was that a selector "must be rediscovering a function of `Gamma`" **because
`Gamma` is a sufficient statistic** -- and `Gamma` is **not** sufficient (§5.2: 3.1-5.8x; §6: up to
209x). The claim survives because the extra information is not *learnable from the signals available to
a selector*: adding five signals buys +0.000 to +0.013 accuracy. The closed form is the right decider
not because its scalar is complete, but because a selector cannot extract more from what it can see.

### 7.3 The stressors: an absolute grid, and a second learner family

The first comparison has a crutch a reviewer should attack: the target grid was scaled per case
(`eps = m * E_floor`), which makes the reachable fraction exactly 1/2 by construction and reduces the
task to estimating `c`. Two changes at once remove it -- the grid becomes **absolute** (one log-spaced
set of targets shared by every case, spanning the corpus's own floor range, so the reachable fraction is
not 1/2 and the task is to estimate the floor's **magnitude**) -- and a **second family** (a depth-3
greedy-Gini CART) joins the logistic regression, with the same features, the same by-matrix split and the
same measured labels:

| format | constant | RULE | LEARN-G | LEARN-X | TREE | overfit gap (train - test) |
|---|---|---|---|---|---|---|
| bf16 | 0.625 | **0.839** | 0.839 | 0.830 | 0.777 | RULE +0.002, TREE **+0.062** |
| fp16 | 0.557 | **0.809** | 0.808 | 0.821 | 0.754 | RULE +0.004, TREE **+0.094** |
| fp32 | 0.572 | **0.829** | 0.829 | 0.830 | 0.832 | RULE +0.007, TREE +0.014 |

The `constant` column is the trivial decider that always answers "reachable": its accuracy equals the
reachable fraction of the absolute grid, which is why it is 0.56-0.63 here and 0.51-0.59 in the
discriminating band below -- low accuracy, and *the number a rule must beat*, not a competitor.

In the **discriminating band** -- targets the corpus reaches 20-80% of the time, about 1,750-2,400
held-out decisions per format -- the rule is best or tied-best in all three: **0.781 / 0.723 / 0.708**
against constants of 0.507 / 0.589 / 0.521, while the CART is worst in two of three.

**P3 survives both stressors.** On the harder task the rule stands 0.21-0.26 above the constant, ties the
learner that sees its own signal, and beats the learner with five extra signals in two formats. The
second family does not extract the missing structure either: **capacity buys nothing, it only overfits** --
the CART has the highest training accuracy of any decider and the lowest test accuracy, with an overfit
gap of 0.062-0.094 against the rule's 0.002-0.007. This is §5/§6's negative re-confirmed on a different
axis: the matrix-specific constant is not in the features a selector can see, and adding inductive bias
does not put it there.

---

## 8. Register lanes: a real degree of freedom that redistributes rather than removes (P5)

Every measurement above is an **isolated dot product**, while the construct is stated for kernels. A real
kernel does not chain one accumulator: it sums into `L` independent register lanes -- fixed by the ISA --
and combines them at the end. The lane model contains the chain as its base case (`L=1` reproduces the
library emulator exactly, asserted), and with an exact register every `L` returns the exact sum, so a
difference at finite precision is a rounding difference and not bookkeeping.

Evaluating the same dot products as matmul elements, median `c = E_floor/(kappa1*u)`:

| format | L=1 | L=2 round-robin | L=4 round-robin | L=8 round-robin | L=8 blocks |
|---|---|---|---|---|---|
| bf16 | 0.4237 | 0.3516 | **0.3062** | 0.3465 | 0.3592 |
| fp16 | 0.5213 | 0.3694 | **0.3427** | 0.3522 | 0.4278 |
| fp32 | 0.6177 | 0.4349 | **0.3869** | 0.3956 | 0.4903 |

Lanes reduce the median constant by **28-37%**, with diminishing returns by `L=4`. But the reduction is
**not a uniform gain**, and reporting only the median would misrepresent it. Per case at `L=4`
round-robin, the outcome splits three ways -- and the split is itself format-dependent, which the median
hides:

| format | improve | unchanged | get worse |
|---|---|---|---|
| bf16 | 30.6% | 55.8% | 13.6% |
| fp16 | 42.5% | 40.4% | 17.1% |
| fp32 | 45.7% | 36.4% | 17.8% |

So in bf16 more than half of all cases are untouched by the extra lanes while one in seven get worse,
whereas in fp16/fp32 the lanes help 42-46% of cases -- a range we quote per format rather than pooled,
because pooling it would state a behaviour two of three formats do not share. The improvement
concentrates almost entirely in the heavily-cancelling cases:

| format | top-quartile `c` cases | (median ratio) | bottom-quartile cases | (median ratio) |
|---|---|---|---|---|
| bf16 | **72.3% improve** | 0.385 | 4.1% | 1.000 |
| fp16 | **88.6% improve** | 0.255 | 7.3% | 1.000 |
| fp32 | **84.7% improve** | 0.274 | 8.3% | 1.000 |

The lane structure **redistributes** the accumulation error rather than removing it: it helps exactly
where the partial sums roam furthest from the total. The **assignment** matters as much as the count:
contiguous blocks (what a naive "split the loop" produces) capture about a third of the round-robin
gain in fp16 and fp32 (0.37, 0.34 of the `L=1 -> L=4` median reduction) and under a sixth of it in bf16
(0.15), so "split the loop" is not a substitute for round-robin assignment. Registered prior **P5 is confirmed in direction and imprecise in form**: "more lanes
reduce the error" holds at the median and fails per case.

**And it is still not the second scalar.** The between-matrix spread at the fixed `kappa1` band survives
**every** lane configuration, 2.1x-5.8x across all of them, never collapsing.

**Figure 4** shows both readings. Panel (a) is the median constant by lane configuration -- the gain is
real and it saturates by `L=4`. Panel (b) is the same arm per case: at `L=4` the lanes improve, leave
unchanged and worsen a three-way split that differs by format, and bf16 -- where more than half the
cases are untouched -- is the clearest evidence that the median alone misrepresents the effect.

![Figure 4 -- register lanes. (a) median constant `c` by lane count and assignment. (b) the per-case three-way split at `L=4` round-robin, which is format-dependent. From `spike_mm_results.json`.](figures/fig4_lanes.png)

---

## 9. External validation: a real library

Everything above is an emulation, so the paper needs a baseline that is not ours. We measure `numpy`'s
own dot product (2.0.2) on the **same pinned matrices** at three formats, with three designs that make
the comparison honest:

- the measurement is **accumulation-only** -- products are rounded by the library itself and the
  reference is their exact rational sum, so product rounding cancels on both sides and what survives is
  the library's accumulation error, comparable to the emulator's accumulation term;
- operands are scaled by a power of two (exact in binary, significand untouched) so full-width operands
  fit the format's range;
- the resolvability bound of §5.3 is applied **on this path too**, because it is a property of the
  quantity rather than of the instrument that first needed it.

| format | median `c` | `c` range | cases inside the emulator's band | slope of `c` vs `n` |
|---|---|---|---|---|
| fp16 | 0.3012 | 0.0152-1.5114 | 57.1% | +0.042 +- 0.184 |
| fp32 | 0.3406 | 0.0006-1.9897 | 53.7% | -0.098 +- 0.170 |
| fp64 | 0.3557 | 0.0073-3.8983 | 56.9% | -0.208 +- 0.108 |

**The constant transfers.** The medians land at 0.30-0.36 in all three formats -- inside the emulator's
independently measured band `[0.27, 1.60]` (§5.2) and near its lower edge, which is what §8's lane
result predicts for a library that uses lanes.

**The `n`-independence is real, and the textbook law is wrong for these cases.** The classical bound is
`gamma_n = n*u/(1 - n*u)`, i.e. an accumulation constant that grows linearly with `n`. Measured over `n`
from 48 to 1107 the slope is `+0.04 +- 0.18 / -0.10 +- 0.17 / -0.21 +- 0.11`, consistent with zero in
every format, and the textbook prediction of `+1.000` is **5.2 / 6.5 / 11.2 standard errors away**. This
is §4.2's flatness reproduced on a real library: the accumulation roundings partially cancel rather than
accumulate coherently, so the error grows like a random walk in the number of adds. A backward-error
bound is an upper bound; this is the measured gap between it and what a kernel does.

**The library's reduction is not a chain.** On the same cases, in the same format, the library is better
than a plain chain on 9-14%, identical on 80-83% and worse on only 6-8% of cases. On a three-term
cancellation the chain and the 4-lane model both return 0.0 where the library returns the exact value.
The library therefore carries more reduction structure than any model in this paper -- which is where
§10 starts.

---

## 10. The second scalar is a structure (and the library is lane-reduced)

### 10.1 The correction this record made to itself

§9's three-term example invites a conclusion, and we drew a wrong one first: the library was described as
carrying a "blocked/pairwise" reduction on the strength of that example. Both halves of that reading are
wrong, and the instrument that refutes it is one probe long.

The triple `[1e8, 1, -1e8]` at fp32 has `kappa1 = 2e8 + 1 > 2^p = 2^24`: **it is exactly the case §5.3's
bound excludes.** The structural claim was read off a case our own filter drops. Measuring it properly,
as relative errors (0.0 = exact):

| case | chain | recursive pairwise | lanes(2) | lanes(4) | library |
|---|---|---|---|---|---|
| `[1e8, 1, -1e8]`, n=3 | 1.0 | 1.0 | **0.0** | **0.0** | **0.0** |
| `[1e8, 0, 1, -1e8]`, n=4 | 1.0 | 1.0 | 1.0 | **1.0** | **1.0** |

The tell that this is **geometry and not precision**: at `n=4` the library is wrong again with the same
magnitudes, which extended precision could not do. What recovers the small term is the lane pairing
`(s0+s2) + (s1+s3) = (1e8 - 1e8) + (1 + 0)`, i.e. **lanes combined by a stride-halving tree**, where the
chain and the recursive halving both add `1` to `1e8` first and lose it.

### 10.2 Which structure reproduces the library

The instrument feeds **every** candidate the same product list in the same order -- so a difference is a
difference of structure, not of terms -- and asks which candidate reproduces the library's **per-case**
error. The subset is the cases where the library actually **rounds**: on the rest every candidate is
exactly right and the comparison is about nothing. "Reproduces" means equal error on that case.

| format | cases where the library rounds | best by reproduction | reproduces | chain reproduces | chain median log-ratio |
|---|---|---|---|---|---|
| fp16 | 142 of 228 | lanes(4) | 71 | 49 | 0.848 |
| fp32 | 185 of 268 | lanes(16) | 160 | 69 | 0.868 |
| fp64 | 194 of 275 | lanes(8) | 125 | 69 | 0.609 |

The library's error is reproduced exactly by a lane structure on 50-86% of the rounding cases against
33-37% for the naive chain. The fitted lane count is **format-specific (4 / 16 / 8)** -- the shape of two
different code paths (a library's own fp16 loop versus a vendor BLAS behind fp32/fp64), not of one
algorithm. The model class is nonetheless honest about its limits: recursive halving, the issue's own
4-lane model and numpy's own block-128/8-lane pairwise sum all fail to reproduce the library, and the
candidates **bracket** it rather than containing it.

### 10.3 The second scalar survives the structure, and is still unidentified

Two readings close the section, and both are negative:

**Fixing the structure does not remove the spread.** At fixed `kappa1 in [1.0, 1.5)`, the spread of `c`
on the same cases:

| format | chain | fitted lane structure | library |
|---|---|---|---|
| fp16 | 692.5x | 395.0x | 181.3x |
| fp32 | 1139.5x | 252.6x | 234.3x |
| fp64 | 2286.0x | 1095.7x | 1661.4x |

Naming the reduction correctly cuts the spread by 2-4.5x and never collapses it, so the spread is not a
chain artefact: **the second scalar exists and is still unidentified**. `r^2(log c, log kappa1)` remains
0.01-0.23 under every structure, so it is not conditioning either.

**The order axis survives the structure change too.** Permuting only the element order (16 permutations,
`kappa1` and the exact sum invariant by construction), the median within-case max/min of the error is
**chain 7.9x / 6.3x (fp32 / fp64) against lanes(4) 5.6x / 3.9x and the library 3.3x / 4.3x**. A lane
structure reduces order sensitivity modestly; it does not remove it. (These figures are far below §6's
78.0x / 209.6x because §6 selects cases for a large floor and this arm selects cases where an order
effect exists at all; the two arms measure different populations and neither replaces the other.)

**Six candidate families for the second scalar are now refuted**: the path-condition family (§6),
per-problem features and a flexible model class (§7.3), register blocking (§8), the naive chain itself,
and the lane structure (§10.3). The negative is a result: it says that a precision-selection rule cannot
be completed by adding a scalar to `Gamma`, and that the remaining variance lives in the matrix's own
value structure and in the reduction the hardware actually performs.

**Figure 5** shows which structure reproduces the library. For each format it plots the fraction of the
library's rounding cases that each candidate structure reproduces exactly: the chain and the pairwise
halving sit far below the lane-reduced trees, and the best lane count moves with the format -- which is
why §10.2 reports two code paths rather than one standard.

![Figure 5 -- which structure reproduces the real library. Fraction of the library's rounding cases reproduced exactly, by candidate reduction structure, for fp16/fp32/fp64. From `spike_struct_results.json`.](figures/fig5_library_structure.png)

---

## 11. Registered prior beliefs, against their outcomes

The five priors and three Heilmeier risks were registered **in writing, before the runs that decided
them**, each with a direction and a justification -- and every registration is carried by a file in this
package, so a reader can check the order rather than take it on trust. P1-P3 are registered in the
issue's public registration body and, in the same words, at the head of `heilmeier.md`. P4 and P5 were
registered later in the study, in the header of the instrument that tested them (`spike_real3.py` and
`spike_mm.py`, both committed, under the heading "REGISTERED PREDICTION (written before measuring)"),
which is where they were written before that instrument was first run. Reporting the priors by outcome
is the honest form of the paper's methodology claim; reporting **where** each was registered is what
makes the claim checkable, because a prior quoted after the result is not a prediction.

| prior | registered direction and justification | outcome |
|---|---|---|
| **P1** the floor exists | error falls with `K` then floors at `~ n*u_accum*kappa`; two known scalings, not a guess | **CONFIRMED** (§4.1) |
| **P2** a single governing scalar | the admission boundary is sharp in `Gamma = n^alpha * u * kappa`, from Higham's `gamma_n` | **REFUTED in its sharp form** (§5.2: a 3.1-5.8x spread at fixed `kappa1`) |
| **P3** a closed form beats learned | a `Gamma`-rule matches a selector cheaply, and its errors concentrate at the boundary | **CONFIRMED, both clauses, but NOT for the registered reason** (§7.2, §7.3) |
| **P4** a path scalar explains the order effect | the path condition number `R = sum|S_k| / sum|a_i b_i|` is the second scalar | **REFUTED** (§6) |
| **P5** register lanes improve accuracy | more lanes reduce the error | **CONFIRMED in direction, IMPRECISE in form** (§8: median -28-37%, but 14-18% of cases worse) |

The registered Heilmeier risks resolved as follows. The primary risk -- "truncation dominates everywhere
and no floor exists" -- **did not materialise**: the floor is present and sharp in all three formats, so
P1's fallback framing was not needed. The second -- the energy axis cannot be measured without hardware --
**did materialise**, and the paper therefore states the law in format-level terms and treats the energy
mapping as a model parameter rather than a measurement; the objective it answers ("energy per trusted
solution") is quoted from the survey [107], not measured here.

Two further registrations deserve explicit mention because they were **refuted before the paper existed**.
The `sqrt(n)` correction to the accumulator-width law (§4.2) was this record's own guess and the
measurement rejected it. And the "blocked/pairwise" mechanism of §10.1 was published in this record's own
notes one round before §10 refuted it. We keep both in the record as evidence for the paper's
methodological claim: the instruments were allowed to contradict their author, and did.

---

## 12. Threats to validity

### 12.1 What the claims do not cover

- **Dot products, not matmuls.** Every controlled measurement is a dot product or a matmul *element*;
  §8 evaluates the kernel shape as `C[i,j] = row_i . row_j`, but a fused kernel's blocking, register
  pressure and instruction scheduling are not modelled. The `K*` and floor statements are therefore about
  the arithmetic, not about a tuned kernel's throughput.
- **Emulation, not a vendor BLAS.** §9 is `numpy`'s dot product on an Apple Accelerate build. It is a
  real library and a real reduction structure, and it is **one** such library: the lane counts of §10.2
  characterise two code paths on one machine, not a standard.
- **`kappa1` is the 1-norm condition number of the operand vectors.** Other condition measures would
  shift the exponents of §5.1; the *insufficiency* result of §5.2 is stated for this one and is not
  claimed for others.
- **Deterministic, single-machine, seeded.** There is no stochastic model in the paper, so there are no
  multi-run statistics to report in the usual sense: the instruments are exact and their outputs are
  byte-identical across runs (§13). Where an estimate has a sampling error we report it (the `beta`
  exponents, the `n`-slopes, the overfit gaps), and where a quantity is exact we do not dress it as a
  sample.
- **The corpus is 14 matrices.** Chosen to span conditioning rather than to be representative, and
  pinned by hash so that the sample cannot drift. The between-matrix spread of §5.2 is a property of
  those 14; the claim is that it is large, not that 3.1-5.8x is its population value.

### 12.2 Where this record corrected itself

Three corrections are part of the evidence that the tiers were not assumed, and they are of two different
kinds.

**A mechanism, retracted by measurement.** §10.1 retracts a mechanism this record had asserted one round
earlier, and the retraction came from applying the record's own resolvability bound (§5.3) to the
record's own example.

**A law, demoted by its own residual.** §5.1's `R^2` fell from 0.49 / 0.93 / 0.95 to
0.64 / 0.47 / 0.61 when the corpus grew from 8 to 14 matrices, which is why the additive reading is
reported as a description rather than as a law. The 8-matrix values are quoted from that round's own
run -- its artefact was replaced when the corpus changed, so this is the one number in the paragraph a
reader has to take on the research record rather than re-derive from the committed files.

**Numbers, re-derived from the artefacts while writing this paper.** Assembling the manuscript, every
figure in §4-§10 was re-read from the committed result files rather than transcribed from the research
notes, and **four blocks disagreed with those notes** -- the conditioning exponents (§5.1), the
path-condition ratios and the within-case correlation median (§6), the per-case lane split (§8), and one
range in §9. The notes had drifted, not the measurements: the correct values are the ones in this paper,
and the notes were corrected in the same pass. We report this because it is the one correction a reader
cannot verify from the paper alone -- it is evidence about the *process*, and the process is part of what
the reproducibility claim is worth.

### 12.3 Why the contribution stands despite them

The bound in §5.3 restricts the claims to a well-defined regime, and inside that regime the paper's
positive results are exact: the floor, `K*`'s dependence on the accumulator width, the quadrature
composition, the 1-bit accuracy of `p*(eps)`, the 78.0x order axis and the lane-reduction percentages are
all measurements against exact arithmetic, reproducible to the byte. The negative results -- `kappa1`'s
insufficiency, the path family, the structure family -- are what a precision-selection rule has to live
with; a rule that assumed any of them would be wrong on 3.1-5.8x of its inputs. And the decision-rule
result is a statement about **cost**: a one-constant closed form matches a learned selector, which is a
practical result independent of whether the constant is theoretically complete.

**Whose belief changes.** (i) A library author who currently spends limbs on a narrow-accumulator kernel
learns that the spend is capped and where the cap is. (ii) A format or hardware architect learns that the
accumulator width, the limb width and the reduction structure are **three** budget axes whose ordering is
not the one the folklore implies -- the reduction structure alone is worth up to 209x, more than a format
step in the cases that matter. (iii) A practitioner running a learned precision selector learns that a
one-constant rule matches it, which changes what the selector is for: not for finding the boundary, but
for finding the cases where the closed form is off by the matrix-specific factor this paper cannot yet
name.

---

## 13. Reproducibility

Every number in this paper is produced by a committed script from committed inputs. The instruments are
deterministic, CPU-only, and use no randomness except where a seed is stated; two consecutive runs of
each instrument produce **byte-identical** result artefacts, and the artefacts' SHA-256 digests are
recorded with the package.

```
# one command: reproduce every result in this paper and check every certificate
bash reproduce.sh
```

Expected output: each instrument runs its own self-test and then the measurement, the figures and the
reference list are regenerated, and the run ends with

```
REPRODUCE: ALL GREEN (17 steps, 0 failures)
```

Tolerance: **exact**. Every instrument asserts that its output file is byte-identical to the committed
one, so a deviation is a failure rather than a drift; `SHA256SUMS.reproduce` carries the 12 result
artefacts, the 5 figures, the built manuscript and the 2 citation documents, and the script checks all
20 digests. `manuscript.md` is a PRODUCT of `manuscript_source.md` and `build_refs.py` -- the source
carries the citations as keys, so the reference list and the >100-cited bar are rebuilt and asserted on
every run rather than trusted. The synthetic instruments need only the Python standard library; the
external-validation arm (§9-§10) needs `numpy` (measured with 2.0.2 under `/usr/bin/python3` 3.9.6) and
the script selects its interpreter by the modules the recompute path actually imports, printing the
versions it used. The corpus is committed and re-hashed on every read, so a cache that has silently
become a different dataset fails the same run. Three further steps are checks rather than
reconstructions, and they are the ones that read what a reader reads: `check_numbers.py` re-derives the
manuscript's headline numbers from the artefacts and matches them against the sentences that state
them; `check_figures.py` asserts that every figure exists at the path the manuscript links, is
embedded, is cited in the prose and names its source artefact; and `refscan126.py --report` rebuilds the
citation-authenticity report and asserts that its numbering is the manuscript's numbering. Each carries
a plant for every certificate, because a certificate that cannot fail is decoration.

---

## 14. Conclusion

Precision selection is usually treated as a search over formats and limb counts. This paper shows that
the search has a hard floor -- the accumulator, not the limb count, sets the reachable accuracy -- that
conditioning is necessary but not sufficient to predict where that floor is, and that a third axis the
folklore treats as a numerical detail, the reduction structure, is worth up to two orders of magnitude in
the cases that matter. A one-constant closed form matches a learned selector on unseen matrices, and the
reason it can is not that its scalar is complete: the missing structure is real (the between-matrix
spread survives every candidate we can name) and is not in the features a selector can see. The paper's
contribution is therefore a boundary plus a well-measured negative: which accuracies are reachable, and
which explanations of *why* are not.

---

## References

[1] Dekker T. J. (1971). A floating-point technique for extending the available precision. DOI: 10.1007/bf01397083. https://doi.org/10.1007/bf01397083
[2] Katsuhisa Ozaki, Yuki Uchino, Toshiyuki Imamura (2025). Ozaki Scheme II: A GEMM-oriented emulation of floating-point matrix multiplication using an integer modular technique. arXiv preprint. https://arxiv.org/abs/2504.08009
[3] Shun-ichiro Hayashi, Daichi Mukunoki, Tetsuya Hoshino, et al. (2026). DGEMM with Ozaki Scheme I/II on FP4 Tensor Cores: A Base-13 E2M1 Limb Representation. arXiv preprint. https://arxiv.org/abs/2608.06812
[4] Erin Carson, Nicholas J. Higham (2018). Accelerating the Solution of Linear Systems by Iterative Refinement in Three Precisions. DOI: 10.1137/17m1140819. https://doi.org/10.1137/17m1140819
[5] Nicholas J. Higham (2002). Accuracy and Stability of Numerical Algorithms. DOI: 10.1137/1.9780898718027. https://doi.org/10.1137/1.9780898718027
[6] James Hardy Wilkinson (2023). Rounding Errors in Algebraic Processes. DOI: 10.1137/1.9781611977523. https://doi.org/10.1137/1.9781611977523
[7] Nicholas J. Higham, Theo Mary (2019). A New Approach to Probabilistic Rounding Error Analysis. DOI: 10.1137/18m1226312. https://doi.org/10.1137/18m1226312
[8] Sahil Bhola, Karthik Duraisamy (2024). Bias- and Variance-Aware Probabilistic Rounding Error Analysis for Floating-Point Arithmetic. arXiv preprint. https://arxiv.org/abs/2404.12556
[9] Sahil Bhola, Karthik Duraisamy (2024). Deterministic and Probabilistic Rounding Error Analysis for Mixed-Precision Arithmetic on Modern Computing Units. arXiv preprint. https://arxiv.org/abs/2411.18747
[10] Jennifer A. Loe, Christian A. Glusa, Ichitaro Yamazaki, et al. (2021). A Study of Mixed Precision Strategies for GMRES on GPUs. arXiv preprint. https://arxiv.org/abs/2109.01232
[11] Eda Oktay, Erin Carson (2021). Multistage Mixed Precision Iterative Refinement. arXiv preprint. https://arxiv.org/abs/2107.06200
[12] Shun-ichiro Hayashi, Daichi Mukunoki, Tetsuya Hoshino, et al. (2026). AWE: Adaptive Weight Encoding for Exact Integer Matrix Products with Fewer GEMMs on FP4 Tensor Cores. arXiv preprint. https://arxiv.org/abs/2609.24519
[13] Eric Hallman, Ilse C. F. Ipsen (2022). Precision-aware Deterministic and Probabilistic Error Bounds for Floating Point Summation. arXiv preprint. https://arxiv.org/abs/2203.15928
[14] Juan Zhang, Yang Zhou (2026). Newton-Based Mixed Precision Iterative Refinement for Large-Scale Sparse Continuous-Time Algebraic Riccati Equations. arXiv preprint. https://arxiv.org/abs/2607.14742
[15] Ahmad Abdelfattah, Hartwig Anzt, Erik G. Boman, et al. (2020). A Survey of Numerical Methods Utilizing Mixed Precision Arithmetic. arXiv preprint. https://arxiv.org/abs/2007.06674
[16] Héctor Martínez, Adrián Castelló, Francisco D. Igual, et al. (2025). The Cambrian Explosion of Mixed-Precision Matrix Multiplication for Quantized Deep Learning Inference. arXiv preprint. https://arxiv.org/abs/2506.11728
[17] W. Kahan (1965). Pracniques: further remarks on reducing truncation errors. DOI: 10.1145/363707.363723. https://doi.org/10.1145/363707.363723
[18] Takeshi Ogita, Siegfried M. Rump, Shin'ichi Oishi (2005). Accurate Sum and Dot Product. DOI: 10.1137/030601818. https://doi.org/10.1137/030601818
[19] James Demmel, Yozo Hida (2004). Accurate and Efficient Floating Point Summation. DOI: 10.1137/s1064827502407627. https://doi.org/10.1137/s1064827502407627
[20] Siegfried M. Rump (2009). Ultimately Fast Accurate Summation. DOI: 10.1137/080738490. https://doi.org/10.1137/080738490
[21] Michael P. Connolly, Nicholas J. Higham, Theo Mary (2021). Stochastic Rounding and Its Probabilistic Backward Error Analysis. DOI: 10.1137/20m1334796. https://doi.org/10.1137/20m1334796
[22] Eric Hallman, Ilse C. F. Ipsen (2021). Deterministic and Probabilistic Error Bounds for Floating Point Summation Algorithms. arXiv preprint. https://arxiv.org/abs/2107.01604
[23] Piyush Sao, Narasinga Miniskar, Pedro Valero-Lara, et al. (2026). A Second-Moment Theory for Floating-Point Reduction Trees. arXiv preprint. https://arxiv.org/abs/2607.18758
[24] Erin Carson, Nicholas J. Higham (2017). A New Analysis of Iterative Refinement and Its Application to Accurate Solution of Ill-Conditioned Sparse Linear Systems. DOI: 10.1137/17m1122918. https://doi.org/10.1137/17m1122918
[25] Eda Oktay, Erin Carson (2022). Mixed Precision GMRES-based Iterative Refinement with Recycling. arXiv preprint. https://arxiv.org/abs/2201.09827
[26] Erin Carson, Noaman Khan (2022). Mixed Precision Iterative Refinement with Sparse Approximate Inverse Preconditioning. arXiv preprint. https://arxiv.org/abs/2202.10204
[27] Noaman Khan, Erin Carson (2023). Mixed Precision Iterative Refinement with Adaptive Precision Sparse Approximate Inverse Preconditioning. arXiv preprint. https://arxiv.org/abs/2307.03914
[28] Erin Carson, Eda Oktay (2024). Mixed Precision FGMRES-Based Iterative Refinement for Weighted Least Squares. arXiv preprint. https://arxiv.org/abs/2401.03755
[29] Bowen Gao, Yuxin Ma, Meiyue Shao (2024). Mixed precision iterative refinement for least squares with linear equality constraints and generalized least squares problems. arXiv preprint. https://arxiv.org/abs/2406.16499
[30] James G. Nagy, Lucas Onisk (2024). Mixed precision iterative refinement for linear inverse problems. arXiv preprint. https://arxiv.org/abs/2409.08335
[31] Jifeng Ge, Juan Zhang (2025). Three-precision iterative refinement with parameter regularization and prediction for solving large sparse linear systems. arXiv preprint. https://arxiv.org/abs/2501.04229
[32] James Quinlan, E. Theodore L. Omtzigt (2024). Iterative Refinement with Low-Precision Posits. arXiv preprint. https://arxiv.org/abs/2408.13400
[33] Jennifer Scott, Miroslav Tůma (2024). Avoiding breakdown in incomplete factorizations in low precision arithmetic. arXiv preprint. https://arxiv.org/abs/2401.17957
[34] Jennifer Scott, Miroslav Tůma (2024). Developing robust incomplete Cholesky factorizations in half precision arithmetic. arXiv preprint. https://arxiv.org/abs/2403.13123
[35] Qiao Chen, Xiangmin Jiao (2021). HIFIR: Hybrid Incomplete Factorization with Iterative Refinement for Preconditioning Ill-conditioned and Singular Systems. arXiv preprint. https://arxiv.org/abs/2106.09877
[36] Boris Krasnopolsky, Alexey Medvedev (2021). XAMG: A library for solving linear systems with multiple right-hand side vectors. arXiv preprint. https://arxiv.org/abs/2103.07329
[37] Zijian Zhang, Rui Hong, Xuesong Chen, et al. (2025). Hybrid-Precision Block-Jacobi Preconditioned GMRES Solver for Linear System in Circuit Simulation. arXiv preprint. https://arxiv.org/abs/2509.09139
[38] Atsushi Suzuki (2022). A Hybrid Factorization Algorithm for Sparse Matrix with Mixed Precision Arithmetic. arXiv preprint. https://arxiv.org/abs/2208.01907
[39] Alexander V. Prolubnikov (2024). Parameter optimization for restarted mixed precision iterative sparse solver. arXiv preprint. https://arxiv.org/abs/2412.08059
[40] Jifeng Ge, Bastien Vieublé, Juan Zhang (2025). Mixed Precision General Alternating-Direction Implicit Method for Solving Large Sparse Linear Systems. arXiv preprint. https://arxiv.org/abs/2512.21164
[41] Erin Carson, Ieva Daužickaitė (2024). Mixed precision sketching for least-squares problems and its application in GMRES-based iterative refinement. arXiv preprint. https://arxiv.org/abs/2410.06319
[42] Weiguo Gao, Yuxin Ma, Meiyue Shao (2022). A mixed precision Jacobi SVD algorithm. arXiv preprint. https://arxiv.org/abs/2209.04626
[43] Bowen Gao, Daniel Kressner, Meiyue Shao (2026). A mixed precision algorithm for the matrix square root. arXiv preprint. https://arxiv.org/abs/2607.12430
[44] Andrii Dmytryshyn, Massimiliano Fasi, Nicholas J. Higham, et al. (2025). Mixed-precision algorithms for solving the Sylvester matrix equation. arXiv preprint. https://arxiv.org/abs/2503.03456
[45] Peter Benner, Xiaobo Liu (2025). Mixed-precision iterative refinement for low-rank Lyapunov equations. arXiv preprint. https://arxiv.org/abs/2510.02126
[46] Stephen F. McCormick, Joseph Benzaken, Rasmus Tamstorf (2020). Algebraic error analysis for mixed-precision multigrid solvers. arXiv preprint. https://arxiv.org/abs/2007.06614
[47] Stephen F. McCormick, Rasmus Tamstorf (2023). Rounding-Error Analysis of Multigrid V-Cycles. arXiv preprint. https://arxiv.org/abs/2307.00216
[48] M. Croci, G. N. Wells (2024). Mixed-precision finite element kernels and assembly: Rounding error analysis and hardware acceleration. arXiv preprint. https://arxiv.org/abs/2410.12614
[49] Michal Habera, Paul T. Kühner, Matteo Croci, et al. (2026). Running error bounds in finite element kernels. arXiv preprint. https://arxiv.org/abs/2609.37844
[50] Issaku Kanamori, Hideo Matsufuru, Tatsumi Aoyama, et al. (2026). Mixed precision solvers with half-precision floating point numbers for Lattice QCD on A64FX processor. arXiv preprint. https://arxiv.org/abs/2602.14450
[51] M. A. Clark, R. Babich, K. Barros, et al. (2009). Solving Lattice QCD systems of equations using mixed precision solvers on GPUs. arXiv preprint. https://arxiv.org/abs/0911.3191
[52] Adela Habib, Joshua Finkelstein, Anders M. N. Niklasson (2024). Efficient Mixed-Precision Matrix Factorization of the Inverse Overlap Matrix in Electronic Structure Calculations with AI-Hardware and GPUs. arXiv preprint. https://arxiv.org/abs/2404.19163
[53] Joshua Finkelstein, Justin S. Smith, Susan M. Mniszewski, et al. (2021). Quantum-based Molecular Dynamics Simulations Using Tensor Cores. arXiv preprint. https://arxiv.org/abs/2107.02737
[54] Joshua Finkelstein, Emanuel H. Rubensson, Susan M. Mniszewski, et al. (2022). Quantum perturbation theory using Tensor cores and a deep neural network. arXiv preprint. https://arxiv.org/abs/2203.09621
[55] Alexandre Benoit (2025). Speeding Up MACE: Low-Precision Tricks for Equivarient Force Fields. arXiv preprint. https://arxiv.org/abs/2510.23621
[56] Tom Kimpson, E. Adam Paxton, Matthew Chantry, et al. (2022). Climate Change Modelling at Reduced Float Precision with Stochastic Rounding. arXiv preprint. https://arxiv.org/abs/2207.14598
[57] Eric B. Ford (2008). Parallel Algorithm for Solving Kepler's Equation on Graphics Processing Units: Application to Analysis of Doppler Exoplanet Searches. arXiv preprint. https://arxiv.org/abs/0812.2976
[58] Richard E. Zeebe (2023). orbitN: A symplectic integrator for planetary systems dominated by a central mass -- Insight into long-term solar system chaos. arXiv preprint. https://arxiv.org/abs/2306.03737
[59] Naigang Wang, Jungwook Choi, Daniel Brand, et al. (2018). Training Deep Neural Networks with 8-bit Floating Point Numbers. arXiv preprint. https://arxiv.org/abs/1812.08011
[60] Dhiraj Kalamkar, Dheevatsa Mudigere, Naveen Mellempudi, et al. (2019). A Study of BFLOAT16 for Deep Learning Training. arXiv preprint. https://arxiv.org/abs/1905.12322
[61] Naveen Mellempudi, Sudarshan Srinivasan, Dipankar Das, et al. (2019). Mixed Precision Training With 8-bit Floating Point. arXiv preprint. https://arxiv.org/abs/1905.12334
[62] Pedram Zamirai, Jian Zhang, Christopher R. Aberger, et al. (2020). Revisiting BFloat16 Training. arXiv preprint. https://arxiv.org/abs/2010.06192
[63] Juyoung Yun, Sol Choi, Francois Rameau, et al. (2023). Revisiting 16-bit Neural Network Training: A Practical Approach for Resource-Limited Learning. arXiv preprint. https://arxiv.org/abs/2305.10947
[64] Robert Hu, Carlo Luschi, Paul Balanca (2025). Elucidating the Design Space of FP4 training. arXiv preprint. https://arxiv.org/abs/2509.17791
[65] Qian Zhao, Kunlong Chen, Changxin Tian, et al. (2026). Rethinking Shrinkage Bias in LLM FP4 Pretraining: Geometric Origin, Systemic Impact, and UFP4 Recipe. arXiv preprint. https://arxiv.org/abs/2606.20381
[66] Mehdi Rahimifar, Amin Darabi, Mehran Taghian Jazi, et al. (2026). Stable FP4 Training via Transposition-Invariant Block Quantization. arXiv preprint. https://arxiv.org/abs/2607.24953
[67] Andrei Panferov, Erik Schultheis, Soroush Tabesh, et al. (2026). Quartet II: Accurate LLM Pre-Training in NVFP4 by Improved Unbiased Gradient Estimation. arXiv preprint. https://arxiv.org/abs/2601.22813
[68] Yu Zhang, Hui-Ling Zhen, Mingxuan Yuan, et al. (2025). MOSS: Efficient and Accurate FP8 LLM Training with Microscaling and Automatic Scaling. arXiv preprint. https://arxiv.org/abs/2511.05811
[69] Hartwig Anzt, Terry Cojean, Goran Flegar, et al. (2022). Ginkgo: A Modern Linear Operator Algebra Framework for High Performance Computing. DOI: 10.1145/3480935. https://doi.org/10.1145/3480935
[70] Daichi Mukunoki (2025). DGEMM without FP64 Arithmetic - Using FP64 Emulation and FP8 Tensor Cores with Ozaki Scheme. arXiv preprint. https://arxiv.org/abs/2508.00441
[71] Tomonori Kouya (2021). Acceleration of multiple precision matrix multiplication based on multi-component floating-point arithmetic using AVX2. arXiv preprint. https://arxiv.org/abs/2101.06584
[72] Denghui Lu, Alexander Maeder, Mathieu Luisier, et al. (2026). EmuGEMM: Fused Tensor Core Kernels for Precision Emulation in Matrix Multiplication. arXiv preprint. https://arxiv.org/abs/2606.25453
[73] Angelika Schwarz, Anton Anders, Cole Brower, et al. (2025). Guaranteed DGEMM Accuracy While Using Reduced Precision Tensor Cores Through Extensions of the Ozaki Scheme. arXiv preprint. https://arxiv.org/abs/2511.13778
[74] Ahmad Abdelfattah, Jack Dongarra, Massimiliano Fasi, et al. (2025). Analysis of Floating-Point Matrix Multiplication Computed via Integer Arithmetic. arXiv preprint. https://arxiv.org/abs/2506.11277
[75] Louis Ledoux, Marc Casas (2024). An Open-Source Framework for Efficient Numerically-Tailored Computations. arXiv preprint. https://arxiv.org/abs/2406.02579
[76] Tomonori Kouya (2026). Performance evaluation of branch-free fused multiply-add algorithms for multi-component-type multiple-precision floating-point arithmetic. arXiv preprint. https://arxiv.org/abs/2607.11391
[77] Fasi Massimiliano, Higham Nicholas J., Mikaitis Mantas, et al. (2021). Numerical behavior of NVIDIA tensor cores. DOI: 10.7717/peerj-cs.330. https://doi.org/10.7717/peerj-cs.330
[78] Faizan A. Khattak, Mantas Mikaitis (2025). Accurate Models of NVIDIA Tensor Cores. arXiv preprint. https://arxiv.org/abs/2512.07004
[79] Peichen Xie, Shuotao Xu, Yang Wang, et al. (2025). Bit-Accurate Modeling of GPU Matrix Multiply-Accumulate Units: Demystifying Numerical Discrepancy and Accuracy. arXiv preprint. https://arxiv.org/abs/2511.10909
[80] Wei Sun, Ang Li, Tong Geng, et al. (2022). Dissecting Tensor Cores via Microbenchmarks: Latency, Throughput and Numeric Behaviors. arXiv preprint. https://arxiv.org/abs/2206.02874
[81] Stefano Markidis, Steven Wei Der Chien, Erwin Laure, et al. (2018). NVIDIA Tensor Core Programmability, Performance & Precision. arXiv preprint. https://arxiv.org/abs/1803.04014
[82] Ziteng Yang, Nicholas J. Riasanovsky, Warren Deng, et al. (2026). Taming Bitwise Behavior in GPU Kernels with Tensor Core: Black-Box Reconstruction, Compiler Enforcement, and Static Verification. arXiv preprint. https://arxiv.org/abs/2609.11356
[83] Xinyi Li, Ang Li, Bo Fang, et al. (2024). FTTN: Feature-Targeted Testing for Numerical Properties of NVIDIA & AMD Matrix Accelerators. arXiv preprint. https://arxiv.org/abs/2403.00232
[84] Field G. Van Zee, Devangi N. Parikh, Robert A. van de Geijn (2019). Supporting mixed-datatype matrix multiplication within the BLIS framework. arXiv preprint. https://arxiv.org/abs/1901.06015
[85] Hiroyuki Ootomo, Katsuhisa Ozaki, Rio Yokota (2023). DGEMM on Integer Matrix Multiplication Unit. arXiv preprint. https://arxiv.org/abs/2306.11975
[86] Danny Hermes (2018). Compensated de Casteljau algorithm in $K$ times the working precision. arXiv preprint. https://arxiv.org/abs/1808.10387
[87] Tomonori Kouya (2013). Practical Implementation of High-Order Multiple Precision Fully Implicit Runge-Kutta Methods with Step Size Control Using Embedded Formula. arXiv preprint. https://arxiv.org/abs/1306.2392
[88] Erin Carson, Xinye Chen (2026). Precision autotuning for linear solvers via contextual bandit-based RL. arXiv preprint. https://arxiv.org/abs/2601.00728
[89] Xinye Chen (2025). Mixed-Precision Conjugate Gradient Solvers with RL-Driven Precision Tuning. arXiv preprint. https://arxiv.org/abs/2504.14268
[90] Ioannis Thanasis, Erin Carson (2026). Error Analysis and Precision Selection for Mixed-Precision DEIM-CUR Decompositions. arXiv preprint. https://arxiv.org/abs/2609.24509
[91] Erez Badash, Dan Boneh, Ilan Komargodski, et al. (2026). Hawkeye: Reproducing GPU-Level Non-Determinism. arXiv preprint. https://arxiv.org/abs/2603.20421
[92] Roman Iakymchuk, Maria Barreda, Stef Graillat, et al. (2020). Reproducibility of Parallel Preconditioned Conjugate Gradient in Hybrid Programming Environments. arXiv preprint. https://arxiv.org/abs/2005.07282
[93] El-Mehdi El Arar, Devan Sohier, Pablo de Oliveira Castro, et al. (2022). The Positive Effects of Stochastic Rounding in Numerical Algorithms. arXiv preprint. https://arxiv.org/abs/2207.03837
[94] Matteo Croci, Michael B. Giles (2020). Effects of round-to-nearest and stochastic rounding in the numerical solution of the heat equation in low precision. arXiv preprint. https://arxiv.org/abs/2010.16225
[95] Lu Xia, Stefano Massei, Michiel E. Hochstenbach, et al. (2022). On the influence of stochastic roundoff errors and their bias on the convergence of the gradient descent method with low-precision floating-point computation. arXiv preprint. https://arxiv.org/abs/2202.12276
[96] Petros Drineas, Ilse C. F. Ipsen (2024). Stochastic Rounding 2.0, with a View towards Complexity Analysis. arXiv preprint. https://arxiv.org/abs/2410.10517
[97] El-Mehdi El Arar, Massimiliano Fasi, Silviu-Ioan Filip, et al. (2026). What is New in Stochastic Rounding: a Survey on Theory, Hardware, and Applications. arXiv preprint. https://arxiv.org/abs/2603.06060
[98] Lu Xia, Martijn Anthonissen, Michiel Hochstenbach, et al. (2020). Improved stochastic rounding. arXiv preprint. https://arxiv.org/abs/2006.00489
[99] Andrew Fitzgibbon, Stephen Felix (2025). On Stochastic Rounding with Few Random Bits. arXiv preprint. https://arxiv.org/abs/2504.20634
[100] El-Mehdi El Arar, Massimiliano Fasi, Silviu-Ioan Filip, et al. (2024). Probabilistic error analysis of limited-precision stochastic rounding. arXiv preprint. https://arxiv.org/abs/2408.03069
[101] El-Mehdi El Arar, Devan Sohier, Pablo de Oliveira Castro, et al. (2022). Stochastic rounding variance and probabilistic bounds: A new approach. arXiv preprint. https://arxiv.org/abs/2207.10321
[102] Pablo de Oliveira Castro, El-Mehdi El Arar, Eric Petit, et al. (2024). Error Analysis of Sum-Product Algorithms under Stochastic Rounding. arXiv preprint. https://arxiv.org/abs/2411.13601
[103] Sami Ben Ali, Silviu-Ioan Filip, Olivier Sentieys (2024). A Stochastic Rounding-Enabled Low-Precision Floating-Point MAC for DNN Training. arXiv preprint. https://arxiv.org/abs/2404.14010
[104] Croci Matteo, Fasi Massimiliano, Higham Nicholas J., et al. (2022). Stochastic rounding: implementation, error analysis and applications. DOI: 10.1098/rsos.211631. https://doi.org/10.1098/rsos.211631
[105] Timothy A. Davis, Yifan Hu (2011). The university of Florida sparse matrix collection. DOI: 10.1145/2049662.2049663. https://doi.org/10.1145/2049662.2049663
[106] Azzam Haidar, Stanimire Tomov, Jack Dongarra, et al. (2018). Harnessing GPU Tensor Cores for Fast FP16 Arithmetic to Speed up Mixed-Precision Iterative Refinement Solvers. DOI: 10.1109/sc.2018.00050. https://doi.org/10.1109/sc.2018.00050
[107] Emmanuel Agullo, Hartwig Anzt, Daniel Bauer, et al. (2026). Mixed-Precision Computing for Scientific Discovery: Formats, Co-Design, and Responsible Approximation. arXiv preprint. https://arxiv.org/abs/2609.37137
