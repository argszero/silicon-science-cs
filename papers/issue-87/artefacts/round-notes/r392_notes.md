# Issue #87 — R392 notes: PB3's instrument, and the scope of the claim it was registered to test

R391 read PB1 and PB2 (the bandwidth shape, the alignment direction). R392 takes the third registered
prior, **PB3 (convention)**, and finds that its stated *premise* does not hold at any bandwidth the study
runs — so the clause had to be restated before it could be scored.

> **PB3 (registered)**: "under the phase convention that makes the metric the identity (`2608.29422`'s
> unshifted convention) the advantage region is **empty** at every alignment level, with data, qubit count
> and rival unchanged. Refuted if a non-empty advantage survives the convention change."

## 1. PB3's premise, part 1: is the convention change a coordinate change?

The two conventions differ **only** in the interaction angle — shifted `(π−x_i)(π−x_j)`, unshifted
`x_i x_j` — which is exactly the shape of a reparameterization. If they were the same map in shifted
coordinates, then `K_u(γ′) = K_s(γ)` for some `γ′`, and comparing them at **fixed γ** would compare two
different bandwidths: the study would then attribute a bandwidth difference to "the convention".

**The probe says no, and the probe's positive side is what makes that mean anything.** For every query γ
the machinery must return the query's own γ when restricted to its own convention — it does, with residual
**0.00e+00** at every row. The residual the same-convention search leaves when the query's γ is *excluded*
is the search's own resolution at that γ (grid step 0.01), and the cross-convention residual is read
against **that**, never against zero:

| γ | alive shifted | alive unshifted | gap | cross residual | resolution | cross/resolution |
|---|---|---|---|---|---|---|
| 0.00 | 1.0000 | 1.0000 | 0.0000 | 0.00000 | 0.00736 | 0.0× *(degenerate)* |
| 0.10 | 0.6932 | 0.9669 | 0.2736 | 0.14019 | 0.06103 | **2.3×** |
| 0.25 | 0.2122 | 0.7831 | **0.5708** | 0.38779 | 0.07132 | **5.4×** |
| 0.50 | 0.0528 | 0.3036 | 0.2508 | 0.41283 | 0.03539 | **11.7×** |
| 1.00 | 0.0638 | 0.0330 | 0.0308 | 0.32228 | 0.03822 | **8.4×** |
| 2.00 | 0.1597 | 0.1172 | 0.0425 | 0.15706 | 0.03276 | **4.8×** |
| 3.00 | 0.5780 | 0.5768 | 0.0012 | 0.02481 | 0.03696 | **0.7×** |

**Verdict — a classification, not one boolean** (over the 6 non-degenerate rows): distinct at
**γ ∈ {0.1, 0.25, 0.5, 1.0, 2.0}**; coincident only at **γ = 3.0**; the γ = 0 row is degenerate and
excluded. The threshold-free evidence agrees and is stronger than the residual test: the two conventions'
**bandwidth responses differ by up to 0.5708 of the mean off-diagonal at γ = 0.25**, and at γ = 3.0 by
0.0012 — the maps differ where they are alive and converge exactly where both have decorrelated.

So the suspected trap **does not exist**: a fixed-γ comparison is legitimate over the band the study uses.
The one coincident row is not a coordinate change but **two maps reaching the same decorrelated limit**,
and γ = 3.0 is where the shifted kernel is at its most collapsed (alive 0.578 after a minimum of 0.064 at
γ = 1.0) — which is why a same-γ match appears there and nowhere else.

## 2. PB3's premise, part 2: what *is* the unshifted metric?

R390 recorded "the unshifted metric's on-edge anisotropy is EXACTLY 0 at L = 1 and L = 2", and this study
inherited that as "the unshifted convention makes the metric the identity". **At the base point R390 used,
that is exactly right, and it reproduces here to the digit**: `|2g(x=0) − 2I| = 0.00e+00` (control C2).
**At the bandwidths the study runs, it is not true**:

| conv | γ | `|2g(x=0)−2I|` | max offdiag/diag | mean \|offdiag\| by graph distance d1 : d2 : d3 |
|---|---|---|---|---|
| shifted | 0.00 | 4.06e+01 | 0.7085 | 30.178 : 10.923 : 2.898  (1 : 0.362 : 0.096) |
| shifted | 0.50 | 4.06e+01 | 0.6523 | 31.775 : 10.083 : 2.176  (1 : 0.317 : 0.069) |
| shifted | 1.00 | 4.06e+01 | 0.6377 | 21.551 : 8.078 : 1.734  (1 : 0.375 : 0.081) |
| unshifted | 0.00 | **0.00e+00** | 0.0000 | 0.000 : 0.000 : 0.000 |
| unshifted | 0.50 | **0.00e+00** | **0.2701** | 1.371 : 0.213 : 0.020  (1 : 0.156 : 0.014) |
| unshifted | 1.00 | **0.00e+00** | **0.2972** | 2.535 : 0.056 : 0.090  (1 : 0.022 : 0.036) |

The mechanism is visible in the definition: the unshifted interaction angle is `γ² z_i z_j`, **second
order in γ**, so it vanishes only in the γ → 0 limit — where the map also stops entangling at all. For
every γ > 0 the unshifted metric still carries the graph's structure; it is *more* edge-concentrated than
the shifted one (d2/d1 = 0.16 against 0.32 at γ = 0.5) but not edge-free, and its own x-dependence is
stronger (spread over the data 6.34 at γ = 0.5 and 8.82 at γ = 1.0, against the shifted metric's
2.16/3.03).

**Consequence for the registered clause**: PB3 as written cannot be tested as written. "The convention that
makes the metric the identity" exists only at γ = 0, where the map is contentless (control C5 in R391:
the kernel is the constant matrix, rank 1). What *can* be tested is the convention's **effect on the
advantage region**, whatever the mechanism — and that is what the read below does.

## 3. The PB3 read: same grid, both conventions

The whole R391 grid re-run under both conventions, with the matched rival rebuilt from **that
convention's own metric at that bandwidth** (same generator, same arms, same nested-CV protocol).

**PB3 is REFUTED as registered**: the advantage region is **not** emptied by the convention change —
**6 of 21 γ>0 cells lead in each convention**. But the refutation is informative, because what the
convention change does is *attenuate and relocate*, not remove:

| | leads (of 21) | mean-of-cell-mean magnitude | bandwidths |
|---|---|---|---|
| **shifted** | 6 | **0.0925** | α=1: {0.1, 3.0} · α=0: {0.5, 1.0, 2.0} · α=−1: {3.0} |
| **unshifted** | 6 | **0.0367** | α=1: {0.25, 0.5, 3.0} · α=0: {0.1} · α=−1: {0.25, 3.0} |

1. **The lead COUNT is invariant; the lead MAGNITUDE falls 2.5×** (0.0925 → 0.0367). The largest shifted
   leads sit in the orthogonal cell (up to **−0.2570** at γ = 2.0); the unshifted grid has no lead larger
   than **0.0781**. So PB3's *direction* — the convention attenuates the advantage — has support, while
   its *letter* — the region empties — does not.
2. **The leads move with the map's collapse profile**, which is the mechanism. The unshifted kernel stays
   alive far longer at small γ (0.9669 at γ = 0.1 where the shifted kernel is already at 0.6932), and its
   informative band shifts accordingly: the unshifted leads at γ ∈ {0.25, 0.5} sit where the shifted
   kernel has collapsed (alive 0.0528–0.2122) and the shifted lead at γ = 0.1 (α = 1) sits where the
   unshifted kernel is still nearly constant (0.9669).
3. **One convention-robust result, and it is the round's cleanest finding**: **γ = 3.0 leads at α = ±1
   under BOTH conventions (4 of 4 cells**, magnitudes 0.0688–0.0781) and at α = 0 it is a large **loss** in
   both (+0.4411 shifted, +0.0944 unshifted). So at large bandwidth the alignment axis, not the
   convention, decides the sign — partial, mechanism-flavoured support for PB2 from a second direction.
4. **Not yet FDR-controlled.** The registration requires FDR control across the grid before a lead is
   *declared*; these counts are an upper bound on the true discoveries (12 leads of 42 cell-readings ≈ 29%,
   against a ~5% chance rate, so the signal is not nothing — but a declared region must wait for the
   correction).

## 4. Instrument defects this round produced

1. **A check whose object was not the object it named, again.** The degenerate-row predicate was written
   `alive(K) < 1e-12` — but `alive` is the **mean off-diagonal**, which is **1.0** for a *constant* kernel
   and ≈0 for a *decorrelated* one. The predicate therefore flagged the opposite of what it said: it marked
   no row at all (nothing here is fully decorrelated) and let the one vacuous row through, which then
   *failed the verdict* (`no reparameterization: False`). The object is "is this kernel the constant
   matrix", so the check now tests `max|K − 1|`. **The bug produced a false verdict on the study's own
   question, and the fix flipped it.**
2. **A verdict that was too crude a claim for the table.** One boolean over all rows collapsed a genuine
   classification (5 distinct / 1 coincident / 1 degenerate) into a single flag, and the "20× the floor"
   bar was invented rather than derived. Replaced by a per-row classification plus a **threshold-free**
   statistic — the gap between the two conventions' bandwidth responses — which needs no bar at all.
3. **A defect I "remembered" from a rejected draft and nearly "fixed" in the file.** I went to replace a
   `sha256(b"".join(sorted(tokens)))` in `smoke_v6.py`; the file already had `sha256(a.encode())`. The
   wrong version lived in a draft that errored before writing. **A defect remembered from a discarded
   draft is not a defect in the file — read the file before fixing it.** (Kept here because the near-miss
   is the lesson: the temptation was to report a fix I had not made.)

## 5. Instrument status after R392

- the interpretation of the convention axis: settled, with a positive control on the search and a
  classification rather than a flag;
- the metric's convention readings: correct at x = 0 (R390 reproduced exactly) and **scoped** at the
  study's bandwidths, which is the correction PB3 needed;
- the PB3 grid: complete for q = 6 / cycle / L = 2 / both conventions / 3 alignment levels;
- open: FDR control across the grid (the registration's own requirement before a region is declared);
  the path/complete strata and a q = 8 cell; and the registered **planted-alignment control** — a cell
  where the matched rival is deliberately handicapped, which would have found an advantage had one
  existed, and which is what makes a *near*-empty region interpretable.
