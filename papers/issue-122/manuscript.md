# Prevention Is Not Cure: What Fresh-Data Rate a Self-Consuming Training Loop Needs to Stay Stable, and What It Needs to Recover

**Contribution level: `theory+empirics`.** This manuscript states an exact mean-field model of the
self-consuming training loop, derives from it three separate boundaries that the literature conflates
into one, and validates every prediction against simulation with planted-truth controls. It is a
theory-plus-empirics study, not a case report: the claims are about the *loop*, a machine-independent
object, and each is accompanied by the instrument that could refute it.

---

## Abstract

A model trained on its own output — the *self-consuming* or *model-collapse* loop — is the subject of
a fast-growing prevention literature, and of a widely quoted folk constant: a fresh-data fraction of
around `1 − λ` is "enough" to keep the loop stable. We show that this literature is measuring **three
different things** and calling them one, and that the most-quoted quantity in it is not a rate at all.

First, the **loop axis**. The folk closed form for the per-generation loss of a symbol,
`(1 − p*)ⁿ`, is neither the loss nor an approximation to it: the loss kernel is *convex* in the
symbol's frequency, and the loop's stationary mean is `p*`, so Jensen's inequality gives
`E[ℓ(q)] ≥ ℓ(p*) = (1 − p*)ⁿ` — the folk formula is a **lower bound on the unconditional loss
probability**, and a loose one. The rate a loop actually experiences is the *conditional* one — the
chance that a symbol now present disappears — and that is a different object. Over 602
well-counted per-symbol readings the bound-to-measured ratio has median 0.08437 and minimum
2.83e-47, so the measured rate is far *above* the bound in 519 of them — and *below*
it in the other 83, by up to 6.03×. Which side a reading lands on is not noise
but a measurable property of the cell: it is the absence fraction of the symbol (readings whose symbol
is absent under 20 % of the time cross the bound in 2 of 202
cases, those absent over 80 % of the time in 27 of 64).
So the folk constant is not merely loose: it is not the same quantity as the loss rate it is quoted
for, and it errs in both directions.

Second, the **protocol axis**. At a *matched* per-generation fresh-data rate, what matters is not the
fraction but the **pool window** `w` — how many generations of history the training set averages over.
Accumulating a pool is far more fragile than replacing it: the same loop's stability boundary falls by
0.00333× (uniform) and 0.00101× (Zipf) when the window `w` grows
from 1 to 64. The mechanism was stated as a prediction before it was measured: pooling turns
exponential mean reversion of rate `λ` into a **moving-average relaxation** whose slowest mode is the
eigenvalue nearest 1 of a degree-`w` companion matrix. Measured rates match that prediction within
2.62% across 12 cells spanning 82.9×, while the rival
replacement law is wrong by up to 32.8×.

Third, the **criterion axis** — the finding we consider most consequential. "Stable" is not one
criterion. Keeping an intact support (a stationary absence rate) and healing a fully collapsed loop (a
first-passage criterion) are **different objects**, and the fresh-data rate they demand differs by
13.4× to 27.6× over the located cells (the one domain-ceiling cell
is excluded). The commonly quoted range of
"fresh-data fraction" in this literature — from about 1 % to about 30 % — is, we argue, mostly a
**criterion artefact**: each number answers a different question.

Two results are negative and we keep them. The loop is **ergodic for every λ > 0**, so there is no
true point of no return — only a finite-horizon one, with hysteresis ratios up to
435× at fixed λ and 96.5% of collapsed
replicates never healing inside a 200-replicate horizon. And **no mechanism quantity is
invariant at the boundary**: the quantities that one might hope to use as a criterion substitute
(relaxation rate, variance, signal-to-noise) each span decades across cells.

The practical answer is a two-number rule: the rate needed to **keep** a loop intact is not the rate
needed to **rescue** one, and they differ by more than an order of magnitude in the regime where
long-context training pools are actually built.

---

## 1. Introduction

Training on model-generated data is now routine: synthetic pre-training corpora, self-distillation,
iterative self-improvement, and replay buffers all close a loop in which the model's outputs become
its future inputs. The literature that studies the failure mode of that loop — *model collapse* — has
grown quickly, and it has converged on a folk prescription: keep a fraction of *fresh* (human) data in
each generation, and the loop stays stable.

That prescription is stated with numbers. A fresh-data fraction of 1 % to 30 % is variously described
as sufficient, and the closed form `(1 − p*)ⁿ` (the probability that a symbol of true frequency `p*`
is missed by `n` draws) is routinely quoted as the per-generation loss. Our study began with a simple
question — *what does a self-consuming loop need to be stable, and what does it need to recover?* — and
found that the question, as usually posed, is under-determined in a way that makes the published
numbers incomparable.

### 1.1 What we find

1. **The folk rate is a lower bound — on a quantity the field does not measure.** `(1 − p*)ⁿ` comes
   from a convex kernel evaluated at the mean (§4.1). It bounds the *unconditional* loss probability,
   not the rate a loop experiences: the measured conditional rate is above the bound in
   519 of 602 well-counted readings and below it in 83, by up to
   6.03×, and which side a reading lands on is predicted by how often its symbol is absent.
2. **The control variable is the window, not the fraction.** With the fresh-data *fraction* held
   fixed per generation, the stability boundary moves by up to three orders of magnitude with the
   length `w` of the training pool's history (§4.2) — and the mechanism is a moving-average
   relaxation whose rate we predict analytically and confirm to 2.62% (§4.3).
3. **There are two boundaries, not one.** The fresh-data rate needed to keep an intact support is
   13.4×–27.6× the rate needed to heal a collapsed
   one, over the located cells, depending only on which criterion you adopt (§4.4). This is, we
   believe, why the literature's quoted numbers disagree by an order of magnitude.
4. **There is no point of no return, only a finite-horizon one.** The loop is ergodic for every
   λ > 0 (§4.5): a fully collapsed loop *can* always heal, but at low λ it does not within any
   horizon a practitioner would wait for (96.5% of collapsed replicates
   never healed within 200 generations at λ = 0.005).

### 1.2 Why this is not just a re-derivation

Each of the three axes is a *measurement* with a stated mechanism and a control that could have
refuted it. The Jensen bound is checked against a planted exact case; the moving-average eigenvalue is
stated as a prediction before the rates are measured; the criterion dependence is demonstrated on
**one** loop with both criteria computed on the same runs; the ergodicity claim is a theorem with a
measured first-passage cross-over in four configurations. The negative results (no invariant
mechanism quantity; no point of no return) are reported as such.

### 1.3 Positioning

This is not the first study of the self-consuming loop, and it is not a survey. Section 5 places it
against the four literatures it touches — the construct itself `[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24]`, the prevention
and mitigation methods `[69, 70, 71, 72, 73, 74, 75, 76, 77, 78]`, the data-mixture and curation literature
`[55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68]`, and the mathematical toolkit it uses `[25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38]` — together with the
mechanism `[39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54]`, measurement `[79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94]` and adjacent-loop
`[95, 96, 97, 98, 99, 100, 101, 102]` families it draws on or departs from. The sharpest single comparison is to
`[9]`, which studies the same loop and quotes a fresh-data threshold: we compute that
threshold under two criteria on the same runs and find that they differ by more than an order of
magnitude. The difference between the two studies is therefore not the phenomenon but **which
question the number answers**.

---

## 2. The construct

### 2.1 The loop

We study the discrete process on the simplex over `K = 8` symbols. Let `p*` be the true
distribution. At generation `t` the model's empirical distribution is `q_t`, and the next generation's
training batch is drawn from a mixture of fresh data and the model's own output:

    N_t ~ Multinomial(n, λ p* + (1 − λ) q_t)
    q_{t+1} = N_t / n

with `λ ∈ (0, 1]` the **fresh-data rate** (per generation), `n` the number of samples per generation,
and `K = 8`. For `λ = 1` the loop is open and `q_{t+1}` is an ordinary multinomial draw; for
`λ → 0` it is closed.

Three symbol distributions are used: `uniform` (all `1/K`), `Zipf(1.2)`, and `twohot` (two symbols at
0.35 each with the remaining 0.30 spread over the rest). All results are from a two-symbol-dominated
regime and a flat one, i.e. neither the easiest nor the hardest case.

### 2.2 The pool protocol

A practitioner controlling the loop does not usually replace the corpus each generation; they
*accumulate*. We model this by a window `w`: the training distribution at generation `t` is the
average of the last `w` generations' empirical distributions,

    r_t = (1/w) Σ_{j=0}^{w−1} q_{t−j},

and the draw uses `λ p* + (1 − λ) r_t`. `w = 1` is the *replacement* protocol (the one assumed by the
folk constant); `w > 1` is *accumulation*. This is the minimal way to separate "how much fresh data
per generation" from "how much history the pool carries" — the two are conflated in the literature,
where a larger pool is often described as merely "more data".

### 2.3 The registration

The direction was registered before any instrument was run, with the following prior beliefs stated in
advance (the registration and its reasoning are in the issue record):

- **P1.** The fresh-data rate needed to *restore* a collapsed loop strictly exceeds the rate needed to
  keep it from collapsing, in every tested configuration, and the ratio between the two grows with the
  depth of collapse.
- **P2.** The prevention boundary is not a function of the fresh-data *fraction* alone: two pool
  policies matched on per-generation fraction but differing in pool history have different boundaries.
- **P3.** Below some rate there is a point of no return: a collapsed loop cannot be restored.

These were chosen to be falsifiable and anchored: P1 and P3 to the **support-loss** mechanism — a
symbol absent from the current model receives no synthetic mass, so its only route back is fresh real
data, which is exactly what the prevention literature's contraction arguments have no reason to track
— and P2 to the 2026 result that the field's contradictory fresh-data fractions are **protocol
artefacts**. Their outcomes are reported in §6.3: one is confirmed, one is refuted, and one is refuted
with its direction reversed.

---

## 3. Method

All instruments are in the package (§Data and code). The measurement protocol is deliberately uniform:

- **Ground truth by construction.** The model is a stochastic process we define, so every quantity is
  computable independently of the simulation. Where a closed form exists we compute it exactly and
  compare; where it does not, we compare two *independent* routes to the same quantity.
- **Controls are planted truth, not identities.** Each instrument carries controls whose expected
  value is known analytically — e.g. at `λ = 0` from a point-mass start, the absence rate of a symbol
  is exactly `(K−1)/K = 0.875`, and the instrument reads 0.875; at `λ = 1`
  the measured loss equals `(1 − p)ⁿ` to within 4.6e-16 relative.
- **Multi-seed statistics.** Every stochastic cell reports 5 seeds with mean and a 95 %
  interval; first-passage cells report 200 replicates with the censoring fraction stated
  beside every number (a censored median is not a median). Seeds are derived from a fixed base
  (20261003) and a hash of the cell's own parameters, never from process state, so a cell can be
  re-run in isolation. The loop sweep covers 108 cells over three symbol distributions,
  `n ∈ {25, 50, 100, 200}` and eight fresh-data rates.
- **Every number in this paper is read out of a committed artefact by a build step** which fails if a
  placeholder has no owner, if a substitution is missed, or if a value is never used.

---

## 4. Results

### 4.1 The loop axis: the folk closed form is a lower bound, not the rate

The kernel that produces a loss of a symbol under the loop is the probability that the symbol is
*sampled zero times* in a generation of `n` draws,

    ℓ_i(q) = (1 − λ p*_i − (1 − λ) q_i)ⁿ,

which is **convex** in `q_i`. The loop's stationary mean is `p*` (the recursion
`E[q_{t+1}] = p* + (1 − λ)(E[q_t] − p*)` is exact), so Jensen's inequality gives

    E[ℓ_i(q)] ≥ ℓ_i(E[q]) = (1 − p*_i)ⁿ     for every i and every λ > 0.

The folk closed form is therefore the **best case**, attained only if the frequency never fluctuates.
It never stops fluctuating: the variance recursion is exact and its fixed point is strictly positive,
so the bound is strict for every `λ < 1`.

That inequality is about the *unconditional* probability: the average of the kernel over all states,
including the states in which the symbol is already absent — where the kernel is close to 1, because a
symbol that is not there is certain to be missed, so `ℓ(0) ≈ 1` and the bound is met with room to
spare. What a loop experiences is the **conditional** rate: the chance that a symbol *now present*
disappears, i.e. the kernel averaged over the generations where the symbol is present. The folk
constant is quoted for that rate and derived from the other one.

Measured against a direct simulation of the loop, over 602 per-symbol readings that pass an
adequacy gate on expected events (`density × rate ≥ 30`, so each reading rests on at least 30 expected
loss events), the bound-to-measured ratio has median 0.08437 and minimum 2.83e-47 —
the measured rate is a median 11.9× *above* the bound. It is not above it everywhere:
83 of the 602 readings sit *below* the bound, by up to 6.03×.

Which side a reading falls on is not noise, and the separating variable is the one that distinguishes
the two objects. Conditioning on presence selects the states with a *high* frequency for the symbol —
a symbol is present because it was drawn, and a symbol drawn often has a small kernel — so the more
often a symbol is absent overall, the more the conditional average is taken over the small-kernel part
of its own marginal:

| absence fraction of the symbol | readings | above the bound | median bound/measured |
|---|---|---|---|
| < 20 % | 202 | 2 | 0.0375 |
| 20–40 % | 115 | 11 | 0.0691 |
| 40–60 % | 106 | 20 | 0.0582 |
| 60–80 % | 115 | 23 | 0.137 |
| > 80 % | 64 | 27 | 0.819 |

The ordering is monotone in the crossing rate and almost monotone in the median. So the folk constant
is not a conservative bound to be tightened but a *different quantity*: for a symbol the loop keeps
almost always, it understates the loss by more than an order of magnitude; for a symbol that is
usually gone, it overstates it. We report the scope because a bound quoted without its scope is a
claim about a quantity no simulation can be blamed for.

The discrepancy grows with `n`, because the closed form collapses exponentially while the measured
loss does not: at `λ = 0.01` on the worst symbol, the measured loss is 0.115122 at `n = 25` and
0.0335235 at `n = 200`, whereas the closed form falls from 0.0354978 to
2.52122e-12.

![Figure 1](figures/fig1_folk_law_refuted.png)

*Figure 1. Left: the measured per-generation loss of the worst symbol (two independent routes) against
the closed form `(1 − p*)ⁿ`, versus `n`. The closed form collapses with `n`; the measured loss does
not. Right: the distribution of the bound-to-measured ratio over the 602 well-counted
readings, with the two sides marked — the bound is below the measured rate (ratio < 1) in
519 of them and above it (ratio > 1) in 83.*

The two independent routes to the same quantity agree to within 39.8% over the same
readings — a disagreement that is a large relative error on the *smallest* readings and is consistent
with the resolution of the gate, which is why it is reported at the gate's own resolution rather than
as a max over all readings.

### 4.2 The protocol axis: the window, not the fraction

We now hold the per-generation fresh-data rate `λ` fixed and vary only the pool window `w`. The
boundary `λ*(w)` — the largest rate at which the worst symbol's stationary absence rate stays at or
below 1 % — falls monotonically with `w` in 4 of 4 configurations:

| source | `n` | `λ*(w=1)` | `λ*(w=4)` | `λ*(w=64)` | ratio `w=64 / w=1` |
|---|---|---|---|---|---|
| uniform | 50 | 0.293701 | 0.0493164 | 0.000976562 | 0.00333 |
| uniform | 200 | 0.0292969 | 0.00805664 | 0.000244141 | 0.00833 |
| Zipf(1.2) | 50 | 1 | 0.382812 | 0.0100098 | 0.01 |
| Zipf(1.2) | 200 | 0.242432 | 0.0419922 | 0.000244141 | 0.00101 |

![Figure 2](figures/fig2_boundary_vs_window.png)

*Figure 2. The stability boundary against pool window, at fixed per-generation fresh-data rate.
Accumulating history is far more fragile than replacing it.*

The practical reading: a system that accumulates its training pool is not "the same loop with more
data". At the same fresh-data budget per generation it is between two and three orders of magnitude
closer to collapse. Conversely, a fresh-data fraction calibrated under a replacement assumption
under-provisions any accumulating pipeline.

### 4.3 The mechanism, predicted before it was measured

Pooling replaces the exponential mean reversion of the replacement protocol with a moving average.
Writing `δ_t = E[q_t] − p*`, the windowed recursion is

    δ_{t+1} = (1 − λ) · (1/w) Σ_{j=0}^{w−1} δ_{t−j},

an order-`w` linear recursion whose asymptotic relaxation rate is the eigenvalue nearest 1 of its
companion matrix. We state this as a prediction and then measure the relaxation rate of the simulated
mean, independently, from the decay of the deviation profile:

| `w` | measured (λ = 0.02) | predicted | measured (λ = 0.05) | predicted |
|---|---|---|---|---|
| 1 | 0.020111 | 0.0202027 | 0.0520015 | 0.0512933 |
| 64 | 0.000626957 | 0.000619606 | 0.00156309 | 0.00156539 |

![Figure 3](figures/fig3_mechanism.png)

*Figure 3. Left: measured relaxation rate against the moving-average companion eigenvalue, for two
fresh-data rates, with the replacement law `−ln(1 − λ)` drawn flat for comparison. Right: the 12
cells of the check on log-log axes.*

Across all 12 cells the worst relative miss is 2.62% while the measured rates span
82.9×. The replacement law is not merely imprecise here: at `λ = 0.05`, `w = 64` it gives
0.0512933 where the loop relaxes at 0.00156309 — wrong by
32.8×, in the direction that makes a practitioner believe the loop is far more
forgiving than it is.

Two controls certify the instrument rather than the claim: `w = 1` reproduces the replacement loop of
§4.1 *exactly* (maximum absolute difference 0 over the compared states), and at
`λ = 1` the measured loss matches the exact `(1 − p)^{wn}` in all window configurations.

### 4.4 The criterion axis: "stable" is two different questions

This is the result we consider most consequential. Take one loop and compute the fresh-data rate it
needs under two criteria that are both natural, both used in the literature, and both reasonable:

- **Prevention criterion** (`λ_stationary`): the largest `λ` at which the *stationary* absence rate of
  the worst symbol is at or below 1 %. "The loop stays intact."
- **Recovery criterion** (`λ_heal`): the smallest `λ` at which a *fully collapsed* loop returns to
  full support within the horizon with probability ≥ 0.5. "The loop can be rescued."

Both boundaries are located by bisection on a log scale with a resolution of
1.4e-06 decades, so each reported boundary is resolved to far finer than the
smallest value it takes.

| source | `w` | `λ_stationary` | `λ_heal` | ratio |
|---|---|---|---|---|
| uniform | 1 | 0.290983 | 0.0105486 | 27.6× |
| uniform | 4 | 0.0504741 | 0.00377383 | 13.4× |
| two-hot | 1 | 1 (domain ceiling) | 0.022173 | 45.1× |
| two-hot | 4 | 0.208994 | 0.00796609 | 26.2× |

![Figure 4](figures/fig4_criterion_dependence.png)

*Figure 4. The two criteria on the same loop. Keeping an intact support costs
13.4×–27.6× more fresh data than healing a collapsed
loop, over the located cells. The hatched bar is a **domain ceiling** — the criterion is unsatisfiable
there, not located, and it is excluded from the range.*

The direction is the one a practitioner would not guess: **prevention is the expensive criterion and
recovery is the cheap one.** A loop that has already collapsed is easier to rescue than a healthy loop
is to protect — because "keep every symbol present at every generation" is a much stronger demand than
"every symbol comes back eventually".

The recovery criterion's underlying measurement is the uncensored probability that a fully collapsed
loop returns to full support within the horizon, `P(heal)`, computed over 5 seeds per cell:

| loop | λ = 0.005 | λ = 0.01 | λ = 0.02 |
|---|---|---|---|
| uniform, `n = 50` | 0.022 (0.00705078–0.0369492) | 0.433 (0.388541–0.477459) | 1 (1–1) |
| two-hot, `n = 50` | 0 (0–0) | 0.017 (0.00661316–0.0273868) | 0.351 (0.295933–0.406067) |
| two-hot, `n = 200` | 0.803 (0.769978–0.836022) | 1.000 | 1.000 |

Two features of this table matter for practice. First, recovery is not a smooth function of the rate:
it is effectively 0/1 in the two-hot `n = 50` row, moving from 0 to
0.351 between λ = 0.005 and λ = 0.02. Second, **more samples per generation
help recovery at fixed rate**: the two-hot loop goes from 0 at `n = 50` to
0.803 at `n = 200` at λ = 0.005, which is the opposite ordering from the
prevention criterion (where a larger `n` makes rare-symbol absence *less* likely but the boundary
comparison is not monotone in `n` across sources).

Each boundary is bracketed by a behavioural two-sided control on functionals that do *not* saturate:
below `λ*/2` the uniform `w = 1` loop holds full support 72.0% of the time, above
`2λ*` 98.2%. The one two-hot `w = 1` cell reads a boundary of exactly 1.0, at the
edge of the parameter domain; it is reported as an **unsatisfiable criterion in the domain** rather
than as a number, and it is not used in the ratio range above — that range is the span over the other
three located cells, 13.4×–27.6×.

### 4.5 Hysteresis: no point of no return, but a horizon you will not wait out

We measure the first-passage time of the *same* event — "all `K` symbols present" — on both sides:
`T_loss` is the exit time from a healthy start, `T_recov` the entry time from a fully collapsed one.
This pairing is what makes the comparison meaningful: the two are times to cross the same set, so a
ratio greater than 1 is hysteresis, and a ratio below 1 says the collapsed state is easier to reach
than to leave.

The four configurations measured, with the censoring fraction printed beside each number (a censored
median is a median over the replicates that finished, which is not the same number):

| source | λ | `T_loss` | `T_recov` | ratio | censored (recovery side) |
|---|---|---|---|---|---|
| uniform | 0.005 | 5.04 | 969.286 | 192× | 0.965 |
| uniform | 0.01 | 4.68 | 996.918 | 213× | 0.575 |
| two-hot | 0.02 | 2.25 | 978.62 | 435× | 0.605 |
| two-hot | 0.005 | 2.005 | *undefined* | *undefined* | 1 |

The last row is the extreme case and it is why we report censoring rather than only medians: at
`n = 50`, λ = 0.005, the two-hot loop leaves full support after a median of
2.005 generations and **not one** of the 200 collapsed replicates
returned within the horizon (censoring 1), so `T_recov` and the ratio are
undefined rather than large. For the uniform loop at the same rate the medians are
5.04 and 969.286 generations — a ratio of
192×, but note that 0.965 of the recovery-side
replicates were censored, so that median is taken over the minority that did recover, and the true
ratio is larger.

![Figure 5](figures/fig5_hysteresis.png)

*Figure 5. Exit and entry first-passage times of the same event, versus fresh-data rate, for the two
distributions measured. The curves cross below λ ≈ 0.2.*

The ratio crosses 1 — hysteresis disappears — in a bracketed range, in all four configurations
measured: uniform `n = 50` between λ = 0.1 and 0.2; uniform
`n = 200` between 0.01 and 0.02; two-hot `n = 50` between
0.5 and 1; two-hot `n = 200` between
0.02 and 0.05.

Because the loop is ergodic for every `λ > 0` — every state communicates with every other — there is
**no point of no return in the strict sense**. What exists is a finite-horizon irreversibility, and
the horizon is set by `λ` and the pool window, not by a qualitative change in the dynamics. Reporting
"collapse is irreversible" without a horizon is a claim about a time budget, not about the process.

### 4.6 What is *not* invariant at the boundary

A tempting shortcut is to replace the boundary computation with a single mechanism quantity. None of
the candidates survives a **held-out** test — each is fitted to the boundary on one distribution and
scored on the other: the moving-average relaxation rate misses by a factor of
164.1 (uniform) and the signal-to-noise ratio of the absence indicator by
39.0% (uniform) and 38.2% (two-hot). The quantities do vary
across the cells — the relaxation rate spans 82.9×, the stationary variance
0.0011–0.01 (a factor of 9.24), the signal-to-noise ratio
1.2–2.1 — but none of them is proportional to `λ*`, and the apparent agreement
of one candidate on one distribution is not reproduced on the other. We report this as a negative
result: the boundary must be measured, not proxied.

---

## 5. Related work

Seven families of work bear on this paper. We state, for each, what we take and where we differ.

**The construct** `[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24]`. The self-consuming loop enters the machine-learning
literature with `[9]` *Self-Consuming Generative Models Go MAD*, which
establishes degeneration under recursive training and the value of retaining real data. The literature
has since quantified it — `[14]` is explicitly about the *rate* of collapse in
recursive training, `[11]` analyses statistically how bad training on
synthetic data is, and `[12]` studies the self-consuming chain for diffusion
finetuning — and surveyed it `[21]`,
`[10]`. Recent work has added a probabilistic framing
`[15]`, spectral diagnostics `[18]`, and an account
tied to replayed sampling noise `[23]`. Two things distinguish this paper.
First, those works quote `(1 − p*)ⁿ`, or a variant of it, as *the* per-generation loss; §4.1 shows it
is a lower bound whose gap grows with `n`, so a trajectory normalised by it overstates how well a loop
is doing. Second, and more consequentially, a fresh-data threshold is quoted without separating
*which* criterion it serves; §4.4 shows that separation is worth up to an order of magnitude on the
same runs. We take the loop itself, and the finding that the failure is distributional rather than a
mere accuracy loss `[19]`, `[20]`.

**Prevention and mitigation** `[69, 70, 71, 72, 73, 74, 75, 76, 77, 78]`. What the field does about collapse is
overwhelmingly *prevention*: stabilisation strategies for co-evolving generative loops
`[76]`, fairness-aware mitigation of the same dynamics
`[73]`, tail-narrowing mitigation in self-improvement
`[74]`, contamination mitigation at evaluation time
`[75]`, `[77]`, and the continual-learning
regularisation family `[69]`, `[70]`,
`[71]`, `[72]`. We have not found one of these
that measures the *recovery* rate of a loop that has already collapsed — the quantity an operator who
has already shipped a self-consuming pipeline needs. Our §4.4 makes the gap concrete: a method
validated on a prevention criterion is validated on the **harder** of the two criteria, so it may
leave the cheap one entirely untested.

**The search form behind this section's absence claims.** Two claims here are absences, and an
absence is only as strong as the search behind it. Both rest on the **arXiv API**
(`export.arxiv.org/api/query`), run on the **scan date 2026-10-03** — the day this package and its
registration were produced. The term harvest that assembled this paper's reference layer carries
**no date filter**, so on the index's only date field, the submission date (`submittedDate`), its
window is **unbounded below** (stated as unbounded, not estimated) and bounded above by the scan
date, i.e. it reaches the whole arXiv index as of that day; the targeted absence queries recorded in
the registration used the same field over the window **2020-01-01 → 2026-10-03**, whose upper
endpoint reaches past the newest work this paper cites. The absences are therefore scoped to **what
arXiv reaches**: a work absent from arXiv, or submitted after the scan date, stands outside them.
Crossref is probed by title in the registration and is not this harvest's index.

**Data mixture, curation, replay and distillation** `[55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68]`. Data-mixing laws
`[67]`, `[68]`, data selection
`[62]`, `[58]`, `[56]`,
deduplication `[65]`, `[66]`, generative replay
`[57]`, `[59]`, `[60]`,
`[61]`, and distillation `[55]`,
`[64]`, `[63]` all treat the training pool as a
*mixture* to be optimised under a budget. §4.2–§4.3 shows that the pool's *history length* is a
first-order control at fixed mixture and fixed budget — a variable this literature does not model, and
one whose mechanism is not a mixture effect at all: it is the moving-average relaxation the pooling
induces, which we write down and confirm to 2.62%.

**The mathematical toolkit** `[25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38]`. The loop's recursion belongs to the branching-
process family, and its finite-state version is amenable to model checking
`[27]`; the tail behaviour of the worst symbol is a local large-deviation
question for a multitype process `[34]`; the question of how uniform the
stationary occupancy of the symbols is, is exactly our §4.4 prevention criterion
`[28]`; the mean-field limit of the interaction `[36]`
gives the recursion we solve in closed form. The support and healing times of §4.5 are hitting-time
problems, for which this literature supplies both the fluid-approximation technique we borrow
`[26]`, `[29]` and scalable estimators
`[38]`, `[37]`. The per-generation law that produces the
loss is a generalized coupon-collector problem `[25]`,
`[30]`, with the Poisson-multinomial object supplying the structure, covering and
transform machinery for the per-symbol counts `[31]`,
`[32]`, `[33]`; the simplex geometry behind the loss
profile is Fisher-Rao `[35]`. The convexity step of §4.1 is the classical
Jensen inequality, applied to the loop's own kernel. The object we add — the eigenvalue of a
degree-`w` companion matrix as the relaxation rate of a *pooled* loop — is not, to our knowledge,
previously applied to this process.

**Mechanism: how support is lost** `[39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54]`. Mode collapse, diversity loss, tail
narrowing and catastrophic forgetting `[41]`, `[39]`,
`[50]`, `[52]` are the phenomena our support
dynamics abstract; the measurement methodology for forgetting
`[44]`, `[53]` and its localisation
`[45]`, `[47]` are the closest relatives of our
absence-of-worst-symbol statistic. We measure a *sequence* of such losses rather than a final state,
which is what makes the hysteresis of §4.5 visible at all.

**Measurement** `[79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94]`. Evaluation-integrity and contamination instruments
`[85]`, `[87]`, `[90]`,
`[94]` supply the methodological stance we adopt — an adequacy gate on
expected events, and a denominator stated with every number. Out-of-distribution and generalisation
instruments `[80]`, `[83]` are the standard
alternatives we did *not* use, because they are insensitive to the absence of a single rare symbol,
which is the quantity that governs collapse.

**Adjacent loops** `[95, 96, 97, 98, 99, 100, 101, 102]`. Continual, online and rehearsal-free adaptation
`[100]`, `[101]`, `[95]`,
`[96]`, `[97]`, `[98]`,
`[99]`, `[99]` run the same data-recycling machinery on
a different object, and `[102]` explicitly studies the dangers of bootstrapping
generation. They are where a no-fresh-data regime is best studied empirically, and therefore the most
likely place in which the criterion split of §4.4 would be observable in an existing system.

## 6. Discussion

### 6.1 The three axes are the answer to "how much fresh data?"

The question "how much fresh data does a self-consuming loop need?" has, we argue, no single answer
because it is three questions wearing one coat:

- **What** is being protected (the *criterion*: intact-support or recoverability) — worth
  13.4×–27.6× (§4.4).
- **How** the data is managed (the *protocol*: replacement or accumulation, i.e. the window `w`) —
  worth up to 0.00101× per unit of the fraction (§4.2).
- **Which** statistic is quoted (the *loop*: the folk lower bound or the measured loss) — worth a
  median 0.08437 on the loss itself (§4.1).

Our reading of the literature's disagreement — fresh-data fractions quoted from about 1 % to about
30 % — is that the spread is dominated by the first of these, because the criterion is usually left
implicit.

### 6.2 Whose belief changes

- **A practitioner building a self-consuming pipeline** should separate the two numbers: the rate that
  protects a healthy loop (much higher than folklore suggests once the pool accumulates) and the rate
  that rescues a collapsed one (much lower). Provisioning to the *prevention* rate at the pool sizes
  actually in use is not conservative — it is the only rate that works.
- **A reader of the prevention literature** should treat every quoted fresh-data fraction as
  under-specified until the criterion and the pool protocol are named.
- **A method author** proposing a new stabiliser should be asked for the recovery criterion as well as
  the prevention criterion; our data show the two do not track each other, so a method that improves
  one may do nothing for the other.

### 6.3 Prior beliefs: outcomes

| prior | registered claim | outcome |
|---|---|---|
| P1 | the rate to *restore* a collapsed loop strictly exceeds the rate to *protect* an intact one, in every configuration, with the ratio growing with collapse depth | **refuted as stated, with the sign reversed.** It holds as a *time* comparison at fixed λ — the ratio 192 at λ = 0.005 — but as a *threshold* comparison it is **backwards**: the prevention rate is the larger, by 13.4×–27.6× over the located cells (§4.4). The two limbs are different objects. |
| P2 | the prevention boundary is not a function of the fresh-data *fraction* alone | **confirmed.** Holding the per-generation fraction fixed and varying only the pool window `w`, the boundary `λ*(w)` falls monotonically in 4 of 4 configurations — to 0.00101× its `w=1` value at `w=64` (the ratio the §4.2 table reports), between two and three orders of magnitude. The control variable is the window, not the fraction. |
| P3 | below some rate there is a point of no return | **refuted in the strict sense, refined in practice.** The loop is ergodic for every λ > 0; irreversibility is finite-horizon (§4.5). |

One confirmation, one refutation, and one refutation whose sign is reversed is, we think, the right
outcome for a registration: the priors were falsifiable and they were tested. The reversal in P1 is
the paper's most surprising result and it was only visible because both criteria were computed on the
same loop; the confirmation in P2 is the paper's headline, and it is the answer to the literature's
own disagreement.

---

## 7. Threats to validity

- **The model is a toy.** The loop is a multinomial re-sampling process over `K = 8` symbols, not
  a neural network trained with gradient descent. Its value is that every quantity is computable and
  the mechanism is exact; its limitation is that a real model's per-token distribution is neither
  stationary nor drawn exactly. What transfers is the *structure* — the Jensen bound, the moving
  average, the criterion dependence — because each is a statement about the re-sampling and pooling
  operations, which are common to both. What does not transfer is any specific constant.
- **Small `K` and two distributions.** Results are reported on `K = 8` with `uniform`,
  `Zipf(1.2)` and `twohot`. The directions are consistent across all three, but the boundary values
  are not universal, and we make no claim that they are. A real language model's tail is heavier than
  any of these.
- **The criterion thresholds are conventions.** "1 % absence" and "full support with probability 0.5"
  are choices. Section 4.4 does not depend on the specific values — it depends on the criteria being
  *different objects* — but a reader adopting other thresholds will get other ratios.
- **The horizon makes collapse look more reversible than it feels.** A 200-generation
  horizon is short for a pre-training run and long for a fine-tuning loop. Every statement about
  recovery in §4.5 is a statement *inside the measured horizon*, and the censoring fraction is printed
  beside every such number for exactly this reason.
- **Reproduction environment.** All instruments run on CPython 3.9.6 with numpy 2.0.2; artefacts are
  byte-identical over repeated runs on that build. Floating-point results may differ in the last ulp
  on another build (CPython 3.12 changed the summation algorithm), which is why every check in the
  package is a tolerance comparison rather than a byte comparison.

**Why this is still worth publishing.** The negative results are as load-bearing as the positive ones:
that there is no point of no return, that no mechanism quantity is invariant at the boundary, and that
the folk constant is a lower bound all *remove* candidate shortcuts that a practitioner might
otherwise rely on. The positive result — that the criterion, not the fraction, dominates the quoted
literature spread — is actionable with no new instrument at all: it is a re-reading of existing
numbers.

---

## 8. Conclusion

A self-consuming training loop is governed by three quantities that the literature conflates into one.
The per-generation fresh-data rate needed to keep a loop intact, the rate needed to rescue a collapsed
one, and the loss kernel's own bound are three different objects; they differ by up to
27.6×, 32.8× and a median 0.08437
respectively. The most-quoted constant in the field is not a rate but a lower bound. Pooling history
— which every real pipeline does — is a far stronger destabiliser than the fresh-data fraction, and it
acts through a moving-average relaxation we can write down and confirm to 2.62%. And
"collapse is irreversible" is true only with a horizon attached.

The practical two-number rule: measure the *prevention* rate for the pool you actually build, and
measure the *recovery* rate separately; do not assume the first protects you or that the second is
unreachable.

---

## Data and code

Everything above is reproduced from the committed package by a single command; the manuscript itself
is assembled from `manuscript.src.md` by `build_manuscript.py`, which resolves every number in this
text from a committed artefact and refuses to build if a number has no owner. Provenance for each
value is in `values.json`.

The reference layer contains 102 references, each verified by identifier against the index
that owns it (102 verified, 102 with author metadata); the citation
report is `reference-check.md`.

## Figures

5 figures accompany this manuscript, each generated from the committed results files by
`make_figures.py` and recorded with its sha256 in `figures/manifest.json`.

## References

*The stated difference closing every entry is its **role class**, not a sentence written per entry; that is a declared convention.* Each entry's closing clause names the family the entry belongs to and the relationship that family bears to this work, and it is generated from the same role assignment that selected the entry (`refs_curate.py`) — so the field states the rule the list was built by and cannot drift from it.  The 102 entries fall into 7 classes (construct 24, theory 14, mechanism 16, protocol 14, prevention 10, measurement 16, adjacent 8).  The per-entry difference is therefore read as: this work is *of* that class, and the class's clause is the difference from this paper.

[1] Chang, F., Wang, H., Chou, C., et al. (2019). *G2R Bound: A Generalization Bound for Supervised Learning from GAN-Synthetic Data*. arXiv:1905.12313. https://arxiv.org/abs/1905.12313 -- a treatment of the self-consuming loop and the failure this paper measures

[2] Nikolenko, S. I. (2019). *Synthetic Data for Deep Learning*. arXiv:1909.11512. https://arxiv.org/abs/1909.11512 -- a treatment of the self-consuming loop and the failure this paper measures

[3] Masarczyk, W., and Tautkute, I. (2020). *Reducing catastrophic forgetting with learning on synthetic data*. arXiv:2004.14046. https://arxiv.org/abs/2004.14046 -- a treatment of the self-consuming loop and the failure this paper measures

[4] Gupta, A., Bhatt, D., and Pandey, A. (2021). *Transitioning from Real to Synthetic data: Quantifying the bias in model*. arXiv:2105.04144. https://arxiv.org/abs/2105.04144 -- a treatment of the self-consuming loop and the failure this paper measures

[5] Muñoz-Cancino, R., Bravo, C., Ríos, S. A., et al. (2022). *Assessment of creditworthiness models privacy-preserving training with synthetic data*. arXiv:2301.01212. https://arxiv.org/abs/2301.01212 -- a treatment of the self-consuming loop and the failure this paper measures

[6] Byrne, S. A., Nyström, M., Maquiling, V., et al. (2023). *Precise localization of corneal reflections in eye images using deep learning trained on synthetic data*. arXiv:2304.05673. https://arxiv.org/abs/2304.05673 -- a treatment of the self-consuming loop and the failure this paper measures

[7] Breugel, B. v., Qian, Z., and Schaar, M. v. d. (2023). *Synthetic data, real errors: how (not) to publish and use synthetic data*. arXiv:2305.09235. https://arxiv.org/abs/2305.09235 -- a treatment of the self-consuming loop and the failure this paper measures

[8] He, Y., Strohmer, T., Vershynin, R., et al. (2023). *Differentially Private Low-dimensional Synthetic Data from High-dimensional Datasets*. arXiv:2305.17148. https://arxiv.org/abs/2305.17148 -- a treatment of the self-consuming loop and the failure this paper measures

[9] Alemohammad, S., Casco-Rodriguez, J., Luzi, L., et al. (2023). *Self-Consuming Generative Models Go MAD*. arXiv:2307.01850. https://arxiv.org/abs/2307.01850 -- a treatment of the self-consuming loop and the failure this paper measures

[10] Mumuni, A., Mumuni, F., and Gerrar, N. K. (2024). *A survey of synthetic data augmentation methods in computer vision*. arXiv:2403.10075. https://arxiv.org/abs/2403.10075 -- a treatment of the self-consuming loop and the failure this paper measures

[11] Seddik, M. E. A., Chen, S., Hayou, S., et al. (2024). *How Bad is Training on Synthetic Data? A Statistical Analysis of Language Model Collapse*. arXiv:2404.05090. https://arxiv.org/abs/2404.05090 -- a treatment of the self-consuming loop and the failure this paper measures

[12] Yoon, Y., Hu, D., Weissburg, I., et al. (2024). *Model Collapse in the Self-Consuming Chain of Diffusion Finetuning: A Novel Perspective from Quantitative Trait Modeling*. arXiv:2407.17493. https://arxiv.org/abs/2407.17493 -- a treatment of the self-consuming loop and the failure this paper measures

[13] Alemohammad, S., Humayun, A. I., Agarwal, S., et al. (2024). *Self-Improving Diffusion Models with Synthetic Data*. arXiv:2408.16333. https://arxiv.org/abs/2408.16333 -- a treatment of the self-consuming loop and the failure this paper measures

[14] Suresh, A. T., Thangaraj, A., and Khandavally, A. N. K. (2024). *Rate of Model Collapse in Recursive Training*. arXiv:2412.17646. https://arxiv.org/abs/2412.17646 -- a treatment of the self-consuming loop and the failure this paper measures

[15] Xu, S., He, H., and Cheng, G. (2025). *A Probabilistic Perspective on Model Collapse*. arXiv:2505.13947. https://arxiv.org/abs/2505.13947 -- a treatment of the self-consuming loop and the failure this paper measures

[16] Shabgahi, S. Z., Aghazadeh, P., Mirhoseini, A., et al. (2025). *ForTIFAI: Fending Off Recursive Training Induced Failure for AI Model Collapse*. arXiv:2509.08972. https://arxiv.org/abs/2509.08972 -- a treatment of the self-consuming loop and the failure this paper measures

[17] Han, Z., Liang, Y., Wang, R., et al. (2025). *Preventing Model Collapse via Contraction-Conditioned Neural Filters*. arXiv:2512.00757. https://arxiv.org/abs/2512.00757 -- a treatment of the self-consuming loop and the failure this paper measures

[18] Gu, Y., Pang, L., Ye, X., et al. (2026). *SIGMA: Scalable Spectral Insights for LLM Model Collapse*. arXiv:2601.03385. https://arxiv.org/abs/2601.03385 -- a treatment of the self-consuming loop and the failure this paper measures

[19] Nielen, T., Ambekar, S., Kiechle, J., et al. (2026). *Entropy Minimization without Model Collapse: Mitigating Prediction Bias in Medical Imaging*. arXiv:2606.02339. https://arxiv.org/abs/2606.02339 -- a treatment of the self-consuming loop and the failure this paper measures

[20] Qiao, X., Du, X., Liu, W., et al. (2026). *When Sample Selection Bias Precipitates Model Collapse*. arXiv:2606.13732. https://arxiv.org/abs/2606.13732 -- a treatment of the self-consuming loop and the failure this paper measures

[21] Xie, X., and Hu, B. (2026). *Reviewing Model Collapse and Countermeasures*. arXiv:2608.21366. https://arxiv.org/abs/2608.21366 -- a treatment of the self-consuming loop and the failure this paper measures

[22] Proskurina, I., Gourru, A., and Velcin, J. (2026). *The Fairness Collapse Phenomenon: Bias Amplification in Language Models Trained on Synthetic Data*. arXiv:2608.04268. https://arxiv.org/abs/2608.04268 -- a treatment of the self-consuming loop and the failure this paper measures

[23] Liu, Y., and Han, Z. (2026). *Break Step: Recursive Training Resonates with Replayed Sampling Noise*. arXiv:2609.11149. https://arxiv.org/abs/2609.11149 -- a treatment of the self-consuming loop and the failure this paper measures

[24] Marchi, M., Silvestre, J. P., Gharesifard, B., et al. (2026). *Preventing Model Collapse: A Fisher-Rao Perspective on the Dynamics of Training with Synthetic Data*. arXiv:2609.18878. https://arxiv.org/abs/2609.18878 -- a treatment of the self-consuming loop and the failure this paper measures

[25] Xu, W., and Tang, A. K. (2010). *A Generalized Coupon Collector Problem*. arXiv:1010.5608. https://arxiv.org/abs/1010.5608 -- theory for the exact chain this paper's recursion belongs to (its stationary law, its tail, or its support)

[26] Gast, N. (2011). *Computing hitting times via fluid approximation: application to the coupon collector problem*. arXiv:1107.3385. https://arxiv.org/abs/1107.3385 -- theory for the exact chain this paper's recursion belongs to (its stationary law, its tail, or its support)

[27] Chen, T., Dräger, K., and Kiefer, S. (2012). *Model Checking Stochastic Branching Processes*. arXiv:1206.1317. https://arxiv.org/abs/1206.1317 -- theory for the exact chain this paper's recursion belongs to (its stationary law, its tail, or its support)

[28] Chakraborty, S., Kamath, A., and Pratap, R. (2013). *Testing Uniformity of Stationary Distribution*. arXiv:1302.5366. https://arxiv.org/abs/1302.5366 -- theory for the exact chain this paper's recursion belongs to (its stationary law, its tail, or its support)

[29] Lang, J., and Henderson, J. (2013). *Efficient Computation of Mean Truncated Hitting Times on Very Large Graphs*. arXiv:1304.4371. https://arxiv.org/abs/1304.4371 -- theory for the exact chain this paper's recursion belongs to (its stationary law, its tail, or its support)

[30] Anceaume, E., Busnel, Y., and Sericola, B. (2014). *New results on a generalized coupon collector problem using Markov chains*. arXiv:1402.5245. https://arxiv.org/abs/1402.5245 -- theory for the exact chain this paper's recursion belongs to (its stationary law, its tail, or its support)

[31] Daskalakis, C., Kamath, G., and Tzamos, C. (2015). *On the Structure, Covering, and Learning of Poisson Multinomial Distributions*. arXiv:1504.08363. https://arxiv.org/abs/1504.08363 -- theory for the exact chain this paper's recursion belongs to (its stationary law, its tail, or its support)

[32] Hasnat, M. A., Velcin, J., Bonnevay, S., et al. (2015). *Simultaneous Clustering and Model Selection for Multinomial Distribution: A Comparative Study*. arXiv:1505.02324. https://arxiv.org/abs/1505.02324 -- theory for the exact chain this paper's recursion belongs to (its stationary law, its tail, or its support)

[33] Diakonikolas, I., Kane, D. M., and Stewart, A. (2015). *The Fourier Transform of Poisson Multinomial Distributions and its Algorithmic Applications*. arXiv:1511.03592. https://arxiv.org/abs/1511.03592 -- theory for the exact chain this paper's recursion belongs to (its stationary law, its tail, or its support)

[34] Doku-Amponsah, K. (2017). *Local Large Deviations: McMillian Theorem for multitype Galton-Watson Processes*. arXiv:1705.09967. https://arxiv.org/abs/1705.09967 -- theory for the exact chain this paper's recursion belongs to (its stationary law, its tail, or its support)

[35] Liang, T., Poggio, T., Rakhlin, A., et al. (2017). *Fisher-Rao Metric, Geometry, and Complexity of Neural Networks*. arXiv:1711.01530. https://arxiv.org/abs/1711.01530 -- theory for the exact chain this paper's recursion belongs to (its stationary law, its tail, or its support)

[36] Stolyar, A. (2022). *A particle system with mean-field interaction: Large-scale limit of stationary distributions*. arXiv:2206.01827. https://arxiv.org/abs/2206.01827 -- theory for the exact chain this paper's recursion belongs to (its stationary law, its tail, or its support)

[37] Zhu, M., Xu, W., Li, W., et al. (2022). *Hitting Times of Random Walks on Edge Corona Product Graphs*. arXiv:2212.05744. https://arxiv.org/abs/2212.05744 -- theory for the exact chain this paper's recursion belongs to (its stationary law, its tail, or its support)

[38] Haris, T., Spaeh, F., Dragazis, S., et al. (2025). *Estimating Hitting Times Locally At Scale*. arXiv:2511.04343. https://arxiv.org/abs/2511.04343 -- theory for the exact chain this paper's recursion belongs to (its stationary law, its tail, or its support)

[39] Kemker, R., McClure, M., Abitino, A., et al. (2017). *Measuring Catastrophic Forgetting in Neural Networks*. arXiv:1708.02072. https://arxiv.org/abs/1708.02072 -- a treatment of how a distribution loses support, diversity or its tail -- the mechanism this paper isolates

[40] Ritter, H., Botev, A., and Barber, D. (2018). *Online Structured Laplace Approximations For Overcoming Catastrophic Forgetting*. arXiv:1805.07810. https://arxiv.org/abs/1805.07810 -- a treatment of how a distribution loses support, diversity or its tail -- the mechanism this paper isolates

[41] Thanh-Tung, H., and Tran, T. (2018). *On Catastrophic Forgetting and Mode Collapse in Generative Adversarial Networks*. arXiv:1807.04015. https://arxiv.org/abs/1807.04015 -- a treatment of how a distribution loses support, diversity or its tail -- the mechanism this paper isolates

[42] Ierusalem, A. (2018). *Catastrophic Importance of Catastrophic Forgetting*. arXiv:1808.07049. https://arxiv.org/abs/1808.07049 -- a treatment of how a distribution loses support, diversity or its tail -- the mechanism this paper isolates

[43] Li, X., Zhou, Y., Wu, T., et al. (2019). *Learn to Grow: A Continual Structure Learning Framework for Overcoming Catastrophic Forgetting*. arXiv:1904.00310. https://arxiv.org/abs/1904.00310 -- a treatment of how a distribution loses support, diversity or its tail -- the mechanism this paper isolates

[44] Pfülb, B., Gepperth, A., Abdullah, S., et al. (2019). *Catastrophic forgetting: still a problem for DNNs*. arXiv:1905.08077. https://arxiv.org/abs/1905.08077 -- a treatment of how a distribution loses support, diversity or its tail -- the mechanism this paper isolates

[45] Wiewel, F., and Yang, B. (2019). *Localizing Catastrophic Forgetting in Neural Networks*. arXiv:1906.02568. https://arxiv.org/abs/1906.02568 -- a treatment of how a distribution loses support, diversity or its tail -- the mechanism this paper isolates

[46] Chen, P. H., Wei, W., Hsieh, C., et al. (2019). *Overcoming Catastrophic Forgetting by Generative Regularization*. arXiv:1912.01238. https://arxiv.org/abs/1912.01238 -- a treatment of how a distribution loses support, diversity or its tail -- the mechanism this paper isolates

[47] Nguyen, G., Chen, S., Do, T., et al. (2020). *Dissecting Catastrophic Forgetting in Continual Learning by Deep Visualization*. arXiv:2001.01578. https://arxiv.org/abs/2001.01578 -- a treatment of how a distribution loses support, diversity or its tail -- the mechanism this paper isolates

[48] Kutalev, A. (2020). *Natural Way to Overcome the Catastrophic Forgetting in Neural Networks*. arXiv:2005.07107. https://arxiv.org/abs/2005.07107 -- a treatment of how a distribution loses support, diversity or its tail -- the mechanism this paper isolates

[49] Yap, P., Ritter, H., and Barber, D. (2020). *Addressing Catastrophic Forgetting in Few-Shot Problems*. arXiv:2005.00146. https://arxiv.org/abs/2005.00146 -- a treatment of how a distribution loses support, diversity or its tail -- the mechanism this paper isolates

[50] Doan, T., Bennani, M., Mazoure, B., et al. (2020). *A Theoretical Analysis of Catastrophic Forgetting through the NTK Overlap Matrix*. arXiv:2010.04003. https://arxiv.org/abs/2010.04003 -- a treatment of how a distribution loses support, diversity or its tail -- the mechanism this paper isolates

[51] Xie, Z., He, F., Fu, S., et al. (2020). *Artificial Neural Variability for Deep Learning: On Overfitting, Noise Memorization, and Catastrophic Forgetting*. arXiv:2011.06220. https://arxiv.org/abs/2011.06220 -- a treatment of how a distribution loses support, diversity or its tail -- the mechanism this paper isolates

[52] Asanuma, H., Takagi, S., Nagano, Y., et al. (2021). *Statistical Mechanical Analysis of Catastrophic Forgetting in Continual Learning with Teacher and Student Networks*. arXiv:2105.07385. https://arxiv.org/abs/2105.07385 -- a treatment of how a distribution loses support, diversity or its tail -- the mechanism this paper isolates

[53] Masarczyk, W., Deja, K., and Trzciński, T. (2021). *On robustness of generative representations against catastrophic forgetting*. arXiv:2109.01844. https://arxiv.org/abs/2109.01844 -- a treatment of how a distribution loses support, diversity or its tail -- the mechanism this paper isolates

[54] Bell, S. J., and Lawrence, N. D. (2021). *Behavioral Experiments for Understanding Catastrophic Forgetting*. arXiv:2110.10570. https://arxiv.org/abs/2110.10570 -- a treatment of how a distribution loses support, diversity or its tail -- the mechanism this paper isolates

[55] Kim, Y., and Rush, A. M. (2016). *Sequence-Level Knowledge Distillation*. arXiv:1606.07947. https://arxiv.org/abs/1606.07947 -- a training-data protocol whose fresh-data fraction and pool history this paper shows are not interchangeable

[56] Peris, Á., Chinea-Rios, M., and Casacuberta, F. (2016). *Neural Networks Classifier for Data Selection in Statistical Machine Translation*. arXiv:1612.05555. https://arxiv.org/abs/1612.05555 -- a training-data protocol whose fresh-data fraction and pool history this paper shows are not interchangeable

[57] Shin, H., Lee, J. K., Kim, J., et al. (2017). *Continual Learning with Deep Generative Replay*. arXiv:1705.08690. https://arxiv.org/abs/1705.08690 -- a training-data protocol whose fresh-data fraction and pool history this paper shows are not interchangeable

[58] Wees, M. v. d., Bisazza, A., and Monz, C. (2017). *Dynamic Data Selection for Neural Machine Translation*. arXiv:1708.00712. https://arxiv.org/abs/1708.00712 -- a training-data protocol whose fresh-data fraction and pool history this paper shows are not interchangeable

[59] Ven, G. M. v. d., and Tolias, A. S. (2018). *Generative replay with feedback connections as a general strategy for continual learning*. arXiv:1809.10635. https://arxiv.org/abs/1809.10635 -- a training-data protocol whose fresh-data fraction and pool history this paper shows are not interchangeable

[60] Mundt, M., Pliushch, I., Majumder, S., et al. (2019). *Unified Probabilistic Deep Continual Learning through Generative Replay and Open Set Recognition*. arXiv:1905.12019. https://arxiv.org/abs/1905.12019 -- a training-data protocol whose fresh-data fraction and pool history this paper shows are not interchangeable

[61] Wang, Z., Subakan, C., Tzinis, E., et al. (2019). *Continual Learning of New Sound Classes using Generative Replay*. arXiv:1906.00654. https://arxiv.org/abs/1906.00654 -- a training-data protocol whose fresh-data fraction and pool history this paper shows are not interchangeable

[62] Coleman, C., Yeh, C., Mussmann, S., et al. (2019). *Selection via Proxy: Efficient Data Selection for Deep Learning*. arXiv:1906.11829. https://arxiv.org/abs/1906.11829 -- a training-data protocol whose fresh-data fraction and pool history this paper shows are not interchangeable

[63] Sucholutsky, I., and Schonlau, M. (2019). *Soft-Label Dataset Distillation and Text Dataset Distillation*. arXiv:1910.02551. https://arxiv.org/abs/1910.02551 -- a training-data protocol whose fresh-data fraction and pool history this paper shows are not interchangeable

[64] Mobahi, H., Farajtabar, M., and Bartlett, P. L. (2020). *Self-Distillation Amplifies Regularization in Hilbert Space*. arXiv:2002.05715. https://arxiv.org/abs/2002.05715 -- a training-data protocol whose fresh-data fraction and pool history this paper shows are not interchangeable

[65] Lee, K., Ippolito, D., Nystrom, A., et al. (2021). *Deduplicating Training Data Makes Language Models Better*. arXiv:2107.06499. https://arxiv.org/abs/2107.06499 -- a training-data protocol whose fresh-data fraction and pool history this paper shows are not interchangeable

[66] Li, X., and Li, J. (2024). *Generative Deduplication For Socia Media Data Selection*. arXiv:2401.05883. https://arxiv.org/abs/2401.05883 -- a training-data protocol whose fresh-data fraction and pool history this paper shows are not interchangeable

[67] Ye, J., Liu, P., Sun, T., et al. (2024). *Data Mixing Laws: Optimizing Data Mixtures by Predicting Language Modeling Performance*. arXiv:2403.16952. https://arxiv.org/abs/2403.16952 -- a training-data protocol whose fresh-data fraction and pool history this paper shows are not interchangeable

[68] Chen, X., Pan, J., Dong, J., et al. (2025). *FoundIR-v2: Optimizing Pre-Training Data Mixtures for Image Restoration Foundation Model*. arXiv:2512.09282. https://arxiv.org/abs/2512.09282 -- a training-data protocol whose fresh-data fraction and pool history this paper shows are not interchangeable

[69] Yin, D., Farajtabar, M., Li, A., et al. (2020). *Optimization and Generalization of Regularization-Based Continual Learning: a Loss Approximation Viewpoint*. arXiv:2006.10974. https://arxiv.org/abs/2006.10974 -- the field's mitigation literature, which is prevention-only and is what this paper is measured against

[70] Pelosin, F., Jha, S., Torsello, A., et al. (2022). *Towards Exemplar-Free Continual Learning in Vision Transformers: an Account of Attention, Functional and Weight Regularization*. arXiv:2203.13167. https://arxiv.org/abs/2203.13167 -- the field's mitigation literature, which is prevention-only and is what this paper is measured against

[71] Gandhi, A., Shah, R. S., Marupudi, V., et al. (2024). *Natural Mitigation of Catastrophic Interference: Continual Learning in Power-Law Learning Environments*. arXiv:2401.10393. https://arxiv.org/abs/2401.10393 -- the field's mitigation literature, which is prevention-only and is what this paper is measured against

[72] Khan, H., Rasool, G., and Bouaynaya, N. C. (2024). *Adversarially Diversified Rehearsal Memory (ADRM): Mitigating Memory Overfitting Challenge in Continual Learning*. arXiv:2405.11829. https://arxiv.org/abs/2405.11829 -- the field's mitigation literature, which is prevention-only and is what this paper is measured against

[73] Mayer, P., Luzi, L., Siahkoohi, A., et al. (2024). *Improving Fairness and Mitigating MADness in Generative Models*. arXiv:2405.13977. https://arxiv.org/abs/2405.13977 -- the field's mitigation literature, which is prevention-only and is what this paper is measured against

[74] Ding, Y., Xi, Z., He, W., et al. (2024). *Mitigating Tail Narrowing in LLM Self-Improvement via Socratic-Guided Sampling*. arXiv:2411.00750. https://arxiv.org/abs/2411.00750 -- the field's mitigation literature, which is prevention-only and is what this paper is measured against

[75] Fan, Y. (2025). *AdEval: Alignment-based Dynamic Evaluation to Mitigate Data Contamination in Large Language Models*. arXiv:2501.13983. https://arxiv.org/abs/2501.13983 -- the field's mitigation literature, which is prevention-only and is what this paper is measured against

[76] Gao, W., and Li, M. (2025). *Convergence Dynamics and Stabilization Strategies of Co-Evolving Generative Models*. arXiv:2503.08117. https://arxiv.org/abs/2503.08117 -- the field's mitigation literature, which is prevention-only and is what this paper is measured against

[77] Anh, L. V., Nguyen, D. D. N., and Nguyen, P. L. (2025). *RN-F: A Novel Approach for Mitigating Contaminated Data in Large Language Models*. arXiv:2505.13249. https://arxiv.org/abs/2505.13249 -- the field's mitigation literature, which is prevention-only and is what this paper is measured against

[78] Liu, S., Liu, W., Xu, Z., et al. (2025). *Towards Mitigation of Hallucination for LLM-empowered Agents: Progressive Generalization Bound Exploration and Watchdog Monitor*. arXiv:2507.15903. https://arxiv.org/abs/2507.15903 -- the field's mitigation literature, which is prevention-only and is what this paper is measured against

[79] Lin, Z., Shi, J., Pathak, D., et al. (2022). *The CLEAR Benchmark: Continual LEArning on Real-World Imagery*. arXiv:2201.06289. https://arxiv.org/abs/2201.06289 -- an instrument or metric for detecting the degradation this paper studies

[80] He, J., and Zhu, F. (2022). *Out-Of-Distribution Detection In Unsupervised Continual Learning*. arXiv:2204.05462. https://arxiv.org/abs/2204.05462 -- an instrument or metric for detecting the degradation this paper studies

[81] Graham, M. S., Pinaya, W. H. L., Tudosiu, P., et al. (2022). *Denoising diffusion models for out-of-distribution detection*. arXiv:2211.07740. https://arxiv.org/abs/2211.07740 -- an instrument or metric for detecting the degradation this paper studies

[82] Soutif--Cormerais, A., Carta, A., Cossu, A., et al. (2023). *A Comprehensive Empirical Evaluation on Online Continual Learning*. arXiv:2308.10328. https://arxiv.org/abs/2308.10328 -- an instrument or metric for detecting the degradation this paper studies

[83] Saha, E., and Tran, G. (2023). *Generalization Bound for Diffusion Models using Random Features*. arXiv:2310.04417. https://arxiv.org/abs/2310.04417 -- an instrument or metric for detecting the degradation this paper studies

[84] Li, Y., Guerin, F., and Lin, C. (2023). *An Open Source Data Contamination Report for Large Language Models*. arXiv:2310.17589. https://arxiv.org/abs/2310.17589 -- an instrument or metric for detecting the degradation this paper studies

[85] Sainz, O., Campos, J. A., García-Ferrero, I., et al. (2023). *NLP Evaluation in trouble: On the Need to Measure LLM Data Contamination for each Benchmark*. arXiv:2310.18018. https://arxiv.org/abs/2310.18018 -- an instrument or metric for detecting the degradation this paper studies

[86] Zhou, K., Zhu, Y., Chen, Z., et al. (2023). *Don't Make Your LLM an Evaluation Benchmark Cheater*. arXiv:2311.01964. https://arxiv.org/abs/2311.01964 -- an instrument or metric for detecting the degradation this paper studies

[87] Golchin, S., and Surdeanu, M. (2023). *Data Contamination Quiz: A Tool to Detect and Estimate Contamination in Large Language Models*. arXiv:2311.06233. https://arxiv.org/abs/2311.06233 -- an instrument or metric for detecting the degradation this paper studies

[88] Li, Y., Guerin, F., and Lin, C. (2023). *LatestEval: Addressing Data Contamination in Language Model Evaluation through Dynamic and Time-Sensitive Test Construction*. arXiv:2312.12343. https://arxiv.org/abs/2312.12343 -- an instrument or metric for detecting the degradation this paper studies

[89] Jiang, M., Liu, K. Z., Zhong, M., et al. (2024). *Investigating Data Contamination for Pre-training Language Models*. arXiv:2401.06059. https://arxiv.org/abs/2401.06059 -- an instrument or metric for detecting the degradation this paper studies

[90] Zhang, H., Lin, Y., and Wan, X. (2024). *PaCoST: Paired Confidence Significance Testing for Benchmark Contamination Detection in Large Language Models*. arXiv:2406.18326. https://arxiv.org/abs/2406.18326 -- an instrument or metric for detecting the degradation this paper studies

[91] Samuel, V., Zhou, Y., and Zou, H. P. (2024). *Towards Data Contamination Detection for Modern Large Language Models: Limitations, Inconsistencies, and Oracle Challenges*. arXiv:2409.09927. https://arxiv.org/abs/2409.09927 -- an instrument or metric for detecting the degradation this paper studies

[92] Wang, Z., Shao, M., Bhandari, J., et al. (2025). *VeriContaminated: Assessing LLM-Driven Verilog Coding for Data Contamination*. arXiv:2503.13572. https://arxiv.org/abs/2503.13572 -- an instrument or metric for detecting the degradation this paper studies

[93] Mehta, S. (2025). *Beyond Surface-Level Similarity: Hierarchical Contamination Detection for Synthetic Training Data in Foundation Models*. arXiv:2511.17602. https://arxiv.org/abs/2511.17602 -- an instrument or metric for detecting the degradation this paper studies

[94] Xiao, X., and Cheng, Y. (2026). *Contamination Inflates Scores but Rarely Reorders Large Language Model Leaderboards*. arXiv:2609.02899. https://arxiv.org/abs/2609.02899 -- an instrument or metric for detecting the degradation this paper studies

[95] Ramapuram, J., Gregorova, M., and Kalousis, A. (2017). *Lifelong Generative Modeling*. arXiv:1705.09847. https://arxiv.org/abs/1705.09847 -- an adjacent loop (online / continual / agentic) that runs the same machinery on a different object

[96] Kim, J., Kim, J., and Kwak, N. (2018). *StackNet: Stacking Parameters for Continual learning*. arXiv:1809.02441. https://arxiv.org/abs/1809.02441 -- an adjacent loop (online / continual / agentic) that runs the same machinery on a different object

[97] Hsu, Y., Liu, Y., Ramasamy, A., et al. (2018). *Re-evaluating Continual Learning Scenarios: A Categorization and Case for Strong Baselines*. arXiv:1810.12488. https://arxiv.org/abs/1810.12488 -- an adjacent loop (online / continual / agentic) that runs the same machinery on a different object

[98] Ven, G. M. v. d., and Tolias, A. S. (2019). *Three scenarios for continual learning*. arXiv:1904.07734. https://arxiv.org/abs/1904.07734 -- an adjacent loop (online / continual / agentic) that runs the same machinery on a different object

[99] Chen, Y., Diethe, T., and Lawrence, N. (2019). *Facilitating Bayesian Continual Learning by Natural Gradients and Stein Gradients*. arXiv:1904.10644. https://arxiv.org/abs/1904.10644 -- an adjacent loop (online / continual / agentic) that runs the same machinery on a different object

[100] Mundt, M., Pliushch, I., and Ramesh, V. (2021). *Neural Architecture Search of Deep Priors: Towards Continual Learning without Catastrophic Interference*. arXiv:2104.06788. https://arxiv.org/abs/2104.06788 -- an adjacent loop (online / continual / agentic) that runs the same machinery on a different object

[101] Smith, J. S., Tian, J., Halbe, S., et al. (2022). *A Closer Look at Rehearsal-Free Continual Learning*. arXiv:2203.17269. https://arxiv.org/abs/2203.17269 -- an adjacent loop (online / continual / agentic) that runs the same machinery on a different object

[102] Zverev, D., Koepke, A. S., and Henriques, J. F. (2025). *On the Dangers of Bootstrapping Generation for Continual Learning and Beyond*. arXiv:2512.11867. https://arxiv.org/abs/2512.11867 -- an adjacent loop (online / continual / agentic) that runs the same machinery on a different object
