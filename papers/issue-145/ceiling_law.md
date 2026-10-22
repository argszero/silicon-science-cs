# The detection ceiling: propositions, proofs, and what identifies it

Issue #145, R674. This file formalises the "detection ceiling" that the registration stated in prose
and that R671 flagged as unsettled. Nothing here is measured on a real population; the propositions
are proved, and the computational check in `ceiling_check.py` verifies them exactly and is
demonstrated to fail on a broken implementation.

## Definitions

Fix a release `r` whose resolved dependency closure is a rooted DAG `(V, E)` with root `r`. A
compromise targets a node `v` at depth `k`, reachable from `r` by a path

    r = v_0 -> v_1 -> ... -> v_k = v.

A verifier holds the published attestation of a package `p` and can obtain the attestation of a
dependency `q` only if `p`'s attestation **names** `q` among its inputs. Define, for each edge
`e_i = (v_{i-1}, v_i)` on the path, the event

    A_i  =  "the attestation of v_{i-1} names v_i as an input",
    c_i  =  P(A_i)                      (the per-edge coverage at that edge).

The verifier **reaches** `v` on this path iff every `A_i` holds, so the detection predicate is

    D = 1  iff  A_1 and A_2 and ... and A_k.

The **detection ceiling at depth `k`** is `P(D = 1)` over the population of depth-`k` nodes.

The one structural fact everything rests on: **a single unnamed edge ends the traversal.** The
verifier cannot learn `v_{i+1}` from `v_{i-1}` without `v_i`'s attestation, and it cannot get `v_i`'s
attestation without `v_{i-1}` naming `v_i`.

## Proposition 1 (definition)

`P(D = 1) = P(A_1 ∩ A_2 ∩ ... ∩ A_k)` — the joint probability of the whole edge set, not a per-edge
quantity. *Proof.* Immediate from the detection predicate. ∎

This is why a paper that reports only per-edge coverage has not stated a ceiling: a joint probability
is not determined by its margins (Proposition 4).

## Proposition 2 (Fréchet upper bound, no assumption)

`P(D = 1) ≤ min_i c_i`. The bound is **attained** when the edges are comonotone — one mechanism
decides every edge together, which is what a single build platform is.

*Proof.* `A_1 ∩ ... ∩ A_k ⊆ A_i` for every `i`, so `P(D) ≤ P(A_i) = c_i` for every `i`; take the
minimum. For attainment, let `U` be uniform on `[0,1]` and set `A_i = {U ≤ c_i}` for all `i`
(comonotone). Then `∩ A_i = {U ≤ min_i c_i}`, so `P(D) = min_i c_i`. ∎

## Proposition 3 (independence)

If the `A_i` are mutually independent, `P(D = 1) = ∏_i c_i`.

*Proof.* Independence multiplies. ∎

**Reading Propositions 2 and 3 together is the correction to my own earlier framing.** R671 recorded
this as a choice between a "per-edge product law" and a "min-law". They are not two candidate laws
about the same quantity: the product is the value under **independence**, the minimum is an
**assumption-free upper bound** attained under **perfect dependence**. They are the two ends of an
interval, and which end applies is a fact about correlation, not a fact about coverage.

## Proposition 4 (the ceiling is not identified by the coverage vector)

For `k ≥ 2` and a coverage vector `c` with every `0 < c_i < 1`, the ceiling ranges over the Fréchet
interval

    max(0, Σ_i c_i − (k − 1))  ≤  P(D)  ≤  min_i c_i,

and **both endpoints are attained by joint laws with exactly the marginals `c`**.

*Proof.* The bounds are the classical Fréchet bounds for the intersection of events with given
marginals. Attainment of the upper end is Proposition 2. Attainment of the lower end is the standard
construction (partition `[0,1]` into `k` blocks whose over-complete overlap realises the Fréchet lower
bound); for the equal-marginal case it is checked exactly in `ceiling_check.py`.
∎

**Consequence, and it is the paper's sharpest statement about its own instrument.** Measuring
per-edge input coverage — which is what this study's construct does — **does not determine the
detection ceiling.** Two populations with identical coverage everywhere can differ in ceiling by a
factor of `2` at `k = 2` and `4` at `k = 3` (computed exactly: `1/4` vs `1/2`, `1/8` vs `1/2` for
`c_i = 1/2`). A coverage measurement is therefore *necessary but not sufficient* for a ceiling claim,
and a ceiling claim must name the correlation structure — in deployed terms, **the builder**.

## Proposition 5 (the first zero dominates)

If any `c_i = 0`, then `P(D = 1) = 0`, for every joint law and every depth `k ≥ i`.

*Proof.* `A_i` has probability zero, so the intersection has probability zero; and it is contained in
every superset. ∎

**This is why the two measured ecosystems cannot separate the regimes, and it is a positive result
rather than a limitation.** npm's attested releases name exactly one input and it is the source commit
(`n = 82`, R670); PyPI's statements carry no input list at all (`n = 119`, R671). Both give `c_i = 0`
on every edge of every path, so by Proposition 5 the ceiling is `0` at every depth under *every*
correlation structure — the Fréchet interval collapses to the single point `{0}`, and independence,
comonotonicity and every mixture between them agree.

So the measured number is robust to the assumption the paper cannot test. That is the honest strength
of the empirical leg: it does not rest on an independence assumption it could not verify.

**And what would identify the ceiling** is now stated exactly: a frame in which some `c_i` lies
strictly between 0 and 1 **and** the correlation across edges is observed — i.e. a population where
more than one builder emits closure-bearing statements, so that the edge events can be seen to move
together or not. Proposition 4 says no amount of extra per-edge coverage data substitutes for that.

## Proposition 6 (why the bound, not the product, is the actionable object)

For a spec author asking "what does a verifier learn about a depth-`k` input", the statement that
holds without any assumption about builder behaviour is Proposition 2's `min_i c_i`, and by
Proposition 5 it is `0` as soon as one edge is unattested. Raising a uniform coverage `c` from `0.1`
to `0.3` multiplies the independence ceiling by `3^k` while leaving the assumption-free bound at `3c`
— which is the precise form of the claim R671 recorded informally as "the first zero dominates".

## What this does and does not establish

- **Established (proved, not measured)**: the ceiling is a joint probability (P1); bounded by the
  minimum coverage and attaining it under comonotonicity (P2); equal to the product under independence
  (P3); **not identified** by the coverage vector, with both endpoints attained at fixed marginals
  (P4); zero as soon as one edge is zero, under every law (P5).
- **Not established**: any ceiling value for a real population. The two ecosystems measured sit at
  the degenerate point where every law agrees, so this leg supplies **no information about
  correlation** in deployed build platforms — only about the value, which is 0.
- **Not claimed**: that deployed attestations are non-conformant. R672 settled that they are
  conformant to their own specifications; this file is about what a *verifier* may infer, which is a
  different question from what a *builder* promised.
