# Issue #87 — R390 notes: the depth item closed, and the metric identified as the Fubini–Study metric

R389 left one open item: its closed form `W = 2 Cov_z(f)` matched the simulator at depth **L = 1** to
0.35% of scale but deviated by **60% of scale at L = 2**, so the round concluded "the closed form is
one-layer; match the rival per depth". R390 shows that conclusion was drawn the wrong way round.

## 1. What was wrong was the formula, not the metric

A parameterised pure state has a metric at every depth: the real part of its quantum geometric tensor,
i.e. the **Fubini–Study metric**

    g_ij(x) = Re<d_i phi|d_j phi> - Re[<d_i phi|phi> conj(<d_j phi|phi>)],

and the fidelity of nearby states obeys `1 - |<phi(x)|phi(x+d)>|^2 = d^T g(x) d + O(|d|^3)`, so

    -2 log K(x, x+d) = 2 d^T g(x) d + O(|d|^3).

R389's `Cov_z(f)` is the **L = 1, x = 0** special case of `g` — measured here to agree with the derived
`g` at **2.5e-16**, i.e. they are the same object symbolically, not merely close. The 60% deviation at
L = 2 was the L = 1 formula being evaluated at L = 2, which says nothing about whether a metric exists.

`arXiv:2608.29422` states this ("the quadratic structure persists at every circuit depth as a pullback of
the Fubini–Study metric"). R390 verifies it on an independent simulator and — more usefully — turns it
into an algorithm: **the metric-matched rival can be built at any depth**, from state derivatives, with no
quantum simulation needed on the classical side.

## 2. How the derivative is taken (exact, not finite-difference)

`T = H U(x)` is unitary, so `|phi_L(x)> = T^L |+>` is normalised for every `x`; `d_i T = H (i d_i theta .
) U(x)`, and by the product rule over the L factors

    d_i |phi_L> = sum_{k=0}^{L-1} T^(L-1-k) (d_i T) T^k |+>.

Cost: O(L²) applications of `T` plus one phase-vector per qubit. `d_i theta` is analytic
(`2 z_i` from the single-qubit term, `-2 (pi - x_j) z_i z_j` per incident edge under the shifted
convention), so nothing is approximated.

## 3. The decisive test, and its result

Two **completely different** computations of the same matrix: (i) the metric *fitted* from the
simulator's `-2 log K(x, x+d)` at one fixed base point (linear + quadratic blocks, symmetric
reconstruction `c_ij / 2` off the diagonal); (ii) `2 x` the *derived* Fubini–Study metric from the state
derivatives. Max relative deviation, in units of the mean `|diagonal|`:

| base point | convention | L = 1 | L = 2 | L = 3 |
|---|---|---|---|---|
| x = 0 | shifted | 5.3e-4 | 1.1e-2 | 2.7e-3 |
| x = random (up to 0.045) | shifted | 5.3e-4 | 1.0e-2 | 4.0e-3 |
| x = 0 | unshifted | 1.1e-3 | 1.1e-3 | — |

The residual of the quadratic expansion is **cubic at every depth** — halving `|d|` divides it by
**7.95–7.99** (8.00 for the unshifted rows) — so the quadratic term is genuinely the leading order and
the agreement above is not a fitted coincidence. The constant is **2**: measured `c = 2.000009` (L = 1),
`2.001228` (L = 2), `1.999538` (L = 3), with `c - 2` falling to zero as `|d| -> 0`.

## 4. Two new facts the study needs, both measured here

**(a) The metric is a FIELD from L = 2 on, not a property of the graph.** Spread of `g` over six random
base points, in units of scale: **L = 1: 0.040**, L = 2: **0.419**, L = 3: 0.257. So at L = 1 a rival
matched to the graph is off by only ~4%, while from L = 2 on a pointwise match is required. R389's
"match per depth" instinct was right about the *practical* consequence and wrong about the reason: the
canonical form is the same at every depth; what changes is that it becomes x-dependent.

**(b) The convention gap is present at every depth (PB3's instrument).** On-edge anisotropy:
shifted **0.636** (L = 1) / **0.709** (L = 2); unshifted **exactly 0.0** at both depths. The unshifted
metric's fit rows agree with `2g` to 1.1e-3, so this is not an artefact of the shifted derivation.

**A control worth keeping**: at `x = 0` under the unshifted convention, `K(L=1)` and `K(L=2)` are equal
to **1e-15** on every deviation tested — an algebraic identity (`theta = 0` there, so `U = I` and the
state collapses). It is why that convention's rows look "too clean" and why a defect hidden by `U = I`
would be invisible in them.

## 5. The defects this round produced, and what caught them

1. **`apply_dT` dropped the `U(x)` factor** — it applied `i d_i theta` to `T^k|+>` instead of to
   `U(x) T^k|+>`. Caught by the central difference (**1.67 relative deviation**) and independently by
   the normalisation identity `Re<d_i phi|phi> = 0` (violated by 0.77; satisfied exactly after the fix).
   **It was invisible in the unshifted rows** because there `theta(x = 0) = 0` makes `U` the identity:
   the wrong term and the right one coincide, and the unshifted rows reported `c = 1.99988` with a clean
   cubic residual while the shifted rows were 167% wrong. A two-arm comparison that shows one arm perfect
   and the other broken is evidence about the **shared** machinery, not about the two arms' difference.
2. **A check whose object was not the object it named**: my C3 asserted `|<d_i phi|phi>| = 0`, which is
   false and should be — the imaginary part is the Berry connection; what normalisation forces to vanish
   is its **real** part. The check failed at 2.14 and the readings were fine.
3. **Claims asserted before being measured** (`c` spread `< 1e-6`, `g` x-independent at L = 1 to 1e-9):
   both were invented thresholds rather than consequences of the physics, and both were wrong. The
   claims now state what the physics says (the constant's limit as `|d| -> 0`; the *ordering* of the
   x-dependence across depths) and are read off the table.

## 6. Instrument status after R390

- exact statevector simulator: verified; state normalised exactly; derivative verified by two independent
  routes (central difference 1.6e-9, normalisation identity exact); whole report byte-identical on rebuild.
- the metric: **identified** — the Fubini–Study metric of the state, at every depth, with `2 x g` matching
  a completely independent fit to 0.05–1.1% of scale.
- the rival: **constructible at any depth from state derivatives** — no simulation needed on the classical
  side, which is what "metric-matched" means operationally.
- open, and next: the generator with the swept alignment parameter and the four rivals; then the first
  cell read of PB1's inverted-U prediction.

Files: `smoke_v4.py` + `smoke_v4_results.json` (this round), plus R389's `smoke_v0..v3.py` — each left as
it ran, so the record shows what each instrument said.
