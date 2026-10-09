# Issue #87 — R389 notes: the smoke test, the four instrument defects it found, and the closed form

Registered this round (R389, 2026-09-20): issue **#87**, label `in-preparation`, with the pool, hotspot
rationale, Heilmeier answers, adversarial checks and registered priors in `heilmeier.md` and in the issue
body. This file is the round's research record: what the smoke test produced.

## 1. What the round set out to do

Before a grid is worth building, the registered direction needs three things: an **exact** simulator of
the entangling feature map, evidence that the induced kernel has a **metric** at small bandwidth (so a
rival can be given the same geometry), and evidence that the metric's anisotropy is a **phase-convention**
artefact (`arXiv:2608.29422`'s two central claims — reproduced here, not quoted).

## 2. Four instrument defects, each found by a control rather than by reading the code

Kept in the order they were found; the earlier files are NOT repaired in place, so the record shows what
each instrument said:

| file | defect | how it showed | what it cost |
|---|---|---|---|
| `smoke_v0.py` | `hadamard_inplace` **returned** the normalised vector while every caller discarded the return value | `K(x,x) = 4096^2 = N^2` instead of 1, and a design with no intercept turned the constant into spurious coefficients | the whole first table |
| `smoke_v0.py` | the metric design carried **quadratic monomials only** | the shifted convention's fit came back with a negative diagonal (`a = -44.5`) | the first anisotropy reading |
| `smoke_v1.py` | the basis regressed was the **signless** Laplacian (D + A) where the structure has the opposite sign | "support MISS" on path/cycle that the complete graph did not show | the second anisotropy reading |
| `smoke_v2.py` | the symmetric reconstruction read `W[i,j] = W[j,i] = c_ij` where the design's monomials are `d_i d_j` with `i <= j`, so the matrix form needs `c_ij / 2` | a **synthetic** response `d^T W_closed d` could not be recovered — off-diagonals came back at exactly **2x** the value handed in | the third anisotropy reading |

The last one is the transferable one: **a regression is an instrument, and it must be tested against a
response built from a matrix you already know before any of its readings are believed.** With the
reconstruction fixed, the recovery control returns the handed matrix to **4.1e-14**.

## 3. The closed form (derived here, verified against the simulator)

`-2 log K = 2 Var_z(theta(x) - theta(x'))` measured to five to six significant digits at bandwidth 0.05.
For the ZZ map with the **shifted** convention the phase difference is, to leading order in the deviation,

    dtheta = sum_i d_i * f_i(z),   f_i(z) = 2 z_i (1 - pi * m_i(z)),   m_i(z) = sum_{j in N(i)} z_j,

so the metric has an **exact closed form as a function of the entanglement graph alone**:

    W = 2 Cov_z(f),

computable by enumerating the 2^q basis states — no simulation, no fit, no bandwidth parameter. Measured
agreement between the fitted metric and this closed form (deviation relative to the mean |diagonal|):
**0.44%** (path), **0.35%** (cycle), **0.34%** (complete), **4.5e-6** (no edges, where the closed form is
exactly `2 I`), and it tightens as the bandwidth falls (0.07% at bandwidth 0.01).

Two refinements over the anchor's statement, both measured:

- **the metric is not edge-supported.** Off-edge entries reach **27%** of the on-edge value (two vertices
  at graph distance 2 are correlated through shared neighbours), so a *metric-matched* classical rival
  must carry the whole covariance matrix, not the graph Laplacian. This is exactly the instrument the
  registered study needs, and fixing it wrong would have handed the rival a weaker geometry than the
  quantum map has.
- **the diagonal is degree-dependent** (mean 22.8 / 28.9 / 143.3 for path / cycle / complete at q = 6),
  i.e. the metric is not "I plus a correction" in a normalization-free way.

The **convention contrast**, measured on the same graph, data and qubit count: anisotropy (max |off-edge
on an edge| over the mean |diagonal|) is **0.636** under the shifted convention and **0.0047** under the
unshifted one — a factor **135** — and the unshifted "metric" is 2.5x less stable across two disjoint
sample sets (1.2e-2 vs 4.9e-3), i.e. under that convention it is a point-dependent quantity rather than a
property of the map. Both readings are the anchor's convention claim, re-measured on an independent
simulator.

## 4. What did NOT carry over (honest open item)

At **depth L = 2** the one-layer closed form deviates by **60%** of scale, and the deviation grows at
L = 3. The derivation above is a one-layer statement; the anchor claims the quadratic structure persists
at every depth as a pullback of the Fubini-Study metric, so the depth case needs its own derivation
rather than an extrapolation. Recorded as the first item of R390 — and it is a *result* about the
instrument, not a defect of the study: it says the study's "metric-matched rival" must be built per
depth, not once.

## 5. Instrument status after this round

- exact statevector simulator: **verified** (K(x,x) = 1 to 4.4e-16, symmetric, PSD; deterministic — the
  whole report is byte-identical on a second build);
- the metric: **closed form in hand** for one layer, verified to < 0.5% on four graphs;
- the rival construction: **feasible** — a Gaussian/derived kernel with an explicitly computed covariance
  matrix, no quantum simulation needed on the classical side;
- open: the depth case, and the ceiling statistic (`arXiv:2609.00475`'s D2) as a predicted axis.

Files: `smoke_v0.py`, `smoke_v1.py`, `smoke_v2.py`, `smoke_v3.py` and their `*_results.json`. Interpreter
coordinate: `/usr/bin/python3` with numpy 2.0.2 (the daemon's own interpreter has no numpy — a coordinate
to declare in the package README when the manuscript is assembled).
