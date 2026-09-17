# Issue #47 — Design freeze (R326, 2026-09-15)

Purpose: fix what the study will claim, and — in the same document — the limits that the claims
must carry into the manuscript. Each limit names the measurement that establishes it, so a limit is
falsifiable rather than an apology. Everything below is downstream of committed artefacts; the
digests are the ones printed by `shasum -a 256` on the files in this directory.

## F0. Frozen artefacts

| artefact | sha256 (first 16) |
|---|---|
| `instrument_v0.py` (harness: generators, costs, grid) | `22654b972adc999d` |
| `paging_v1.py` (repaired per-page attachment) | `349820afff8551e3` |
| `sufficiency_v1.py` (scalar-vs-signed design, step 6) | `5bc7d2f49c78d28d` |
| `sufficiency_v1_results.json` | `27d5dc487a7e90ba` |
| `external_cell_v1.py` (external anchor cell, step 7) | `3d21412ecaaaf5ba` |
| `external_cell_v1_results.json` | `e4416ae15f3f6aa3` |
| `external_cell_mutation_v1.py` (check-liveness control) | `461f20a18a7d36a5` |
| `external_cell_mutation_v1_results.json` | `89342bcd4ef628cd` |

Reproduction status: both `sufficiency_v1.py` and `external_cell_v1.py` produce byte-identical
results across full re-runs; `external_cell_mutation_v1.py` re-runs to the identical verdict table.
The external cell gates 13 checks and reports X2 (reach) as a measurement, not a gate.

## F0b. Amendment after registration (R335, 2026-09-16) — the certificate stage

The registered design left success metric **(c)** — the lambda-calibration loss, reported as a factor
with a 95% between-stream interval — without a stage to measure it, and the first submission of the
reproduction package therefore reported (c) as `UNMET`: a *state*, not a number. The stage
`lambda_cert_v1.py` now computes the registered quantity (the certificate rule `lam_wc(eta)` and the
per-profile factor `ratio(lam_wc)/ratio(lam*)`), and the canonical runner recomputes every number the
manuscript quotes from the per-profile primitives of its artefact.

What this amendment does **not** change: no registered prior, no claim in F1, and no scope limit in
F2. The prior P2 recorded at registration (*the gap grows with the tail*) is now measurable, and it
comes out **half confirmed** — tail profiles carry the higher mean factor in all three problems,
while the correlations are weak and the relation is non-monotone in spread. That is a result about
the prior, not a change to it, and the criterion's own wording ("a factor with a 95% between-stream
interval") is met as registered.

The two files this amendment adds are kept outside the frozen table below on purpose: that table is
the record of what was registered, and a post-registration addition is checked separately — and named
here — rather than folded into it.

- `lambda_cert_v1.py` — sha256 (first 16) `ed13c418ef7ee1f7`
- `lambda_cert_v1_results.json` — sha256 (first 16) `054bb3a2ef7cfcea`

## F1. The three claims that survive the freeze

1. **A scalar prediction error is not sufficient.** Constructive witness, not a p-value: two arms
   with the *same* multiset of |error|, one all-positive and one all-negative, have identical
   `mean_abs`, `sd` and `q95_abs` **by construction** (max gap `0.00e+00`, asserted), while the
   realised loss differs by up to `-0.5679` (ski, `unbiased_extreme`; cluster MDE `0.0187`; 16/16
   replicates; 31/39 blocks exceed their own cluster MDE). No model-selection question remains: a
   loss that is not a function of the scalar cannot be predicted from it.
2. **When the signal is resolvable, the sign channel carries information beyond the scalar.** Per
   decision object, held out by profile, matched **in form** (both arms two terms, contrasting one
   odd term): cluster-MDE advantage `+1.48` (ski), `+2.61` (sched), `+0.97` (paging, unresolved).
3. **The published ordering survives contact with the harness's own ordering — in sign, not in
   magnitude.** The external anchor (`arXiv:2608.27975`, LAH / S4-FIFO) reports a *concordant* pair:
   the cache with the larger mean gain (+26% over S3-FIFO vs the derived +16.7% over 3L-Cache) is
   also the one with the smaller worst-trace degradation over FIFO (0.8% vs 8.8%). The harness
   reproduces the sign of that concordance in all three problems: Kendall tau of mean gain against
   tail, `ski 0.744`, `paging 0.889`, `sched 1.000`; without the zero-error anchor (extreme on both
   axes by construction) `0.697 / 0.873 / 1.000`.

## F2. Scope limits (frozen; each with the measurement that establishes it)

**L1 — the paging attachment is model-dependent.** Two attachments are possible: a step-common
multiplier on every candidate's score, and a per-page multiplier. The step-common attachment is
**provably blind to positive errors** — a common factor cannot change an argmax, so it reproduces the
zero-error cost exactly (C5a: 32/32 traces, and it is only exact when the error vector never clamps).
The per-page attachment differs on the same information (C5b: 31/32) and is the one used. Therefore
any statement about *positive-bias* predictions in paging is a statement about the per-page
attachment, not an attachment-free fact. C5c reports the size of the trap: profiles that are
positive **biases** are not non-negative **multipliers** (`over_extreme` still changes the shared
attachment's cost on 6/32 traces, through clamping — a positive bias is not a positive multiplier).

**L2 — the null of the object-level design is shifted, so negative verdicts are uninterpretable.**
The specificity control — an even synthetic target with no sign dependence — penalises the odd
parameter by ~13 cluster MDEs (ski `-12.95`, sched `-13.12`, paging `-1.53`). A design that punishes
its own odd term under a sign-free target cannot be read as evidence *against* a signed model from a
negative result. Frozen consequence: only the **positive** resolutions in claim 2 are reported as
evidence; paging's `+0.97` and every negative reading are reported as unresolved, and the unmatched-form reading is retired -- its sign is not even stable across problems
(ski -9.16, sched +6.62, paging -3.70), which is what a form confound looks like. This is a limit on the *instrument*, not on the
claim.

**L3 — unit reach is uneven, and the cell says where.** Measured against FIFO, the published
robustness scale is a worst-trace degradation of 0.8–8.8%. The harness reaches that scale in **ski**
(12 of 13 profiles at or above 0.8%, 11 at or above 8.8%) and in **neither paging nor sched** (0 of
13; the worst unit in those problems is *better* than FIFO at every profile: paging min `-0.4060`,
sched min `-0.3080`). So in those two problems the generated errors are uniformly gentler than a real
predictor's errors, and the cell supports **no** claim about the consequences of the published
magnitude there — only about the ordering sign (claim 3). Reported as `REPORT X2/reach_per_problem`
because it is a property of the harness, not of it: an always-green gate would be decoration.

**L4 — concordance is a rank/sign agreement, not a magnitude match.** No unit conversion is
attempted or claimed (the registration's fallback clause: anchor to the published numbers and report
the residual). The anchor's numbers are transcribed from the arXiv record re-verified this round
(HTTP 200, title match); the +16.7% comparison mean is **derived** (`1.26 / 1.08 - 1.0`) and the
derivation is written into the artefact rather than asserted as a value.

**L5 — the generalising unit is the profile, not the repeated measurement.** The MDE recomputation in
step 6 showed the earlier figure was optimistic by 3.7–6.3× because it was computed over paired
*units* that share the error generator, implementation and fit. Every resolution verdict in this
study therefore quotes the **cluster** unit (profile, replicate).

**L6 — synthetic harness, real anchor.** All losses come from `instrument_v0`'s generators; the
external cell anchors ordering and reach against a published system, and is not a reproduction of
that system's numbers.

## F3. Not frozen (work that the claim set still needs)

- the reproduction package (one command, expected output, digests) — nine stages now, the
  certificate stage of the F0b amendment included;
- ≥100 references, each genuinely cited, each verified against Crossref/arXiv (`reference-check.md`);
- contribution-level declaration, prior-belief reporting, and the manuscript itself;
- an independent re-run from a foreign working directory (coordinates supplied silently by the
  authoring machine).
