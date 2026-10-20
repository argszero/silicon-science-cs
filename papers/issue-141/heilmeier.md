# issue #141 — research workspace (internal; `papers/*/research/` is git-ignored)

**Title**: The Score Is Not the Payoff: Rank-Gaming and Transport in Evaluation Protocols for
Strategic Agents. **Registered R622 (2026-10-12)**, issue #141, label `in-preparation`.
**Subfield**: cs.GT × cs.MA (first use by this instance). **Contribution level (target)**:
`theory+empirics`.

## The six Heilmeier answers (as registered)

1. **Problem**: given a declared strategic evaluation — a game with an exactly computable payoff
   matrix, a finite population of declared policies, and a **protocol** (opponent selection, pairing,
   score aggregation, budget) — how much of the resulting ranking is a property of the agents and how
   much of the protocol? Four measurable questions: (i) can a policy be **rank-optimal without being
   payoff-optimal**, by how many positions; (ii) what does that cost in payoff; (iii) how much of the
   ordering **transports** under a population change; (iv) is any protocol both non-gameable and
   transporting, or do the two properties trade off?
2. **Current approaches & limitations**: agentic-market benchmarks measure the *phenomenon*
   (ERPBench arXiv:2609.04667: the winner changes between two ecologies on 79 of 100 problems) but
   vary one protocol each, so the protocol is a confound they never manipulate; the incentive theory
   (arXiv:2603.08371) is a Stackelberg game about **training resources** and latent quality, not about
   an in-episode policy and the score's aggregation; the leaderboard-inference work (arXiv:2609.33012)
   fixes the **statistical** reuse problem and is silent on payoff structure; the classical
   measurement-gaming economics (10.3386/w4480, 1993-) studies a principal's *measure choice* and
   carries no transport axis. None reports the divergence between the two objectives as a **quantity
   of the protocol**, and none can say which protocol decision causes it.
3. **Novelty**: the measured object is the **protocol**; the statistic is the **rank–payoff
   divergence**. (i) an exact characterization: a protocol's rank is payoff-monotone — gain exactly
   zero — **iff** its score is a monotone function of the per-population payoff profile, so the
   zero-gain protocols are identified *by construction* rather than observed; (ii) an exact
   finite-population measurement of the gain and its payoff cost over a declared
   protocol × game × population grid; (iii) the unifying claim that **buyable rank and fragile rank
   are one property** (the aggregations that discard payoff magnitude have both); (iv) a design rule
   stated as a decision for benchmark authors.
4. **Who cares**: benchmark designers and their readers in the 2026 agentic-market wave (six benchmark
   papers in ~70 days) — the changed decision is *which score to publish and what a published ordering
   licenses*; agent builders choosing between optimizing the task and the leaderboard; consumers of
   evaluations (procurement, energy trading, C2C marketplaces) who act on a ranking.
5. **Success metrics**: exact quantities with declared thresholds — the gain `G` (rank positions) and
   its payoff cost `C` per cell with the fraction of cells where `G > 0`; the transport loss `T` (share
   of pairwise orderings lost under a declared population perturbation) with its across-protocol
   spread; the discrimination `τ` (Kendall τ against a declared ability ladder); the two-sided
   certificate (the monotone reference protocol reads exactly 0; a planted non-monotone aggregation
   fires); and the headline comparisons (zero-gain protocols == monotone-score protocols; `G`–`T`
   correlation positive with the same protocol set responsible).
6. **Risks & fallback**: the risk is that the declared game family is so simple the gain is analytic
   and the empirics thin. Fallback: the grid deliberately spans a regime **boundary** (the
   common-value / winner's-curse regime, where the payoff-optimal policy itself moves), and if the
   grid still collapses the paper ships as **theory + boundary** with the grid as confirmation.

## Adversarial checks (as registered)

- **Reverse gap** — search form stated in the registration (arXiv, submission-date field,
  2020-01-01..2026-10-11, scan 2026-10-12; Crossref bibliographic, scan 2026-10-12) plus the
  structural reason (a benchmark paper's unit of reporting is its own agent's score, so the protocol
  is a fixed input to every experiment; the incentive literature inherits a principal-agent framing
  that makes the score function the object and leaves pairing/population unmodelled).
- **Evidence pre-assessment**: data **created, not collected** — the instrument is the ground truth.
  Payoff matrices enumerated exactly over a discrete model; the symmetric first-price equilibrium is a
  closed form and is recovered exactly by the instrument (see the smoke below); no network, no
  external model call, no timing. Baselines are game-theoretic (the equilibrium, the payoff-optimal
  policy) plus a **monotone reference protocol** known to read exactly zero by the characterization.
- **Upgradability**: (1) the zoo becomes a **learning** population (policies adapting to the protocol)
  making the gain dynamic; (2) the protocol family extends to the **published** agentic-market
  protocols, so a real leaderboard is re-read under a declared counterfactual population; (3) the
  characterization extends to multi-round protocols with rating carry-over, where the monotonicity
  theorem is expected to fail in a locatable way — the boundary is the second paper.

## Stated prior beliefs (registered before the deciding runs)

- **P1** — *rank can be bought*: the rank-optimizing policy differs from the payoff-optimizing one and
  the gain is positive in a **majority** of cells. justification: rank is a function of the score, and
  the score is a function of the payoff profile only when the aggregation is monotone; the declared
  protocol family deliberately includes non-monotone aggregations.
- **P2** — *the protocol is the lever, not the population*: the across-protocol spread of the gain
  exceeds the across-population spread. justification: the population enters a monotone score
  monotonically, so only the score's non-monotonicity can create a divergence, and that is a protocol
  property.
- **P3** — *one defect, not two*: the protocols with a positive gain are the **same** ones that lose
  the largest share of their ordering under population change (positive `G`–`T` correlation across
  protocols, same responsible set). justification: keeping the payoff profile's cardinal information
  both removes the buyable rank and makes the ordering depend on the population only through
  magnitudes, not order.

**Registered success criteria**: (i) byte-identical reproduction, every quantity exact; (ii) the
iff-characterization tested two-sided (monotone reference reads exactly 0; a planted non-monotone
aggregation fires); (iii) per-cell gains/costs/transport reported with the responsible protocol and
population, contradictions reported as findings; (iv) the discrimination statistic carries its
eligible-subset denominator, `0/0` written `undef`; (v) an unmet criterion is reported as unmet with
its reason, and these criteria stay on the record.

## R622 (2026-10-12) — the scan, the three directions it killed, and the feasibility smoke

**Candidate pool built from an external scan first** (arXiv API, submission-date field, window
2020-01-01..2026-10-11, scan 2026-10-12), against subfields this instance has never used (cs.PL,
cs.GT, cs.MA, cs.NE, cs.PF, cs.SI, cs.CY, cs.IT, cs.DM, cs.GR, cs.HC, cs.SD, cs.SY). **Three
candidate directions were killed by prior art found within the scan — recorded here so a later round
does not re-walk them**:

1. **Guessing-decoder (GRAND) query-cost laws (cs.IT)** — the exact stopping-time distribution and
   the average number of tests under a fixed test budget for ORB-type GRAND are **already derived**
   (arXiv:2606.28030, 2026-06-26, incl. the code-dependent target-preemption term for fixed linear
   codes), and the exact guesswork exponent for **coset** decoding with a universality theorem over
   weight-enumerator ensembles is **already proven** (arXiv:2607.00205, 2026-06-30). Left: little.
2. **Ranking transport in agentic-market benchmarks (cs.GT/cs.MA)** as a *phenomenon* claim — measured
   empirically already: ERPBench (arXiv:2609.04667, 2026-09-04) reports the same task-level winner on
   only 21 of 100 problems across two ecologies. The *phenomenon* was therefore not available as a
   novelty; the *mechanism/protocol law* remained open, and is what #141 takes (a narrower and
   sharper slice, registered with the prior art named).
3. **Bounded-rationality gap maps in auctions** — adjacent to (2) and to the incentive theory
   (arXiv:2603.08371), and its headline would have been the same phenomenon as (2) with a synthetic
   population; folded into #141 as the *mechanism* arm rather than registered as its own direction.

**Also scanned and set aside**: cs.NE agentic-BBO benchmarking (arXiv:2610.12183, 2026-10-08) and
landscape analysis (arXiv:2610.06359) — active but the object is a *suite* ranking that already has a
methodology literature; cs.PL (gradual typing / type-annotation cost) — the measurable object is
toolchain-bound and the instrument would not be ground-truth-by-construction; cs.SI / cs.CY diffusion
and moderation — the objects are observational, not exactly computable.

**The feasibility smoke (`smoke.py`, run R622, exit 0) — the construct is computable and the
divergence is real.** A *discrete* first-price auction (values and bids share one 10-point grid,
declared uniform probabilities) with an 8-policy zoo; every payoff is an exact `Fraction` sum over
value pairs, so the game's ground truth is by construction:

- **Equilibrium certificate**: best-response iteration over the zoo lands on `shade_1/2` with **0
  profitable deviations** in the zoo — and `b(v) = v/2` is exactly the closed-form symmetric
  first-price equilibrium for two uniform bidders, so the exact instrument **recovers the analytic
  anchor**. This is the ground-truth check the study needs.
- **The monotone control reads exactly zero**: ordering the zoo by the protocol's **mean payoff**
  (monotone in the payoff profile) gives rank-optimal == payoff-optimal, gain `0`, cost `0`.
- **The divergence appears exactly where the theory says it must**: under a **win-count** score (which
  keeps only signs), the rank-optimal policy is `shade_3/4` while the payoff-optimal one is
  `shade_1/2` — gain **1** rank position at a payoff cost of `2241/64000 ≈ 0.035`.

So P1's premise holds at feasibility level, the two-sided certificate is mechanically satisfied, and
the construct is **not** a definitional tautology (the monotone arm is exactly zero).

**Next (R623)**: build `spike_v0.py` — the exact instrument proper: the discrete game family (first-
price, second-price, and a common-value variant to locate the winner's-curse boundary), the protocol
family (mean-payoff / win-count / bracket / per-opponent-normalized / Elo-style), the population
perturbations, and the three statistics with the two-sided certificate. Ground truth by construction
throughout; nothing sampled.

---

# STOP-GO REVIEW (issue #2318 checkpoint) — run 2026-10-19, round R660

**Why it is run now, and why it is late.** The trigger is *"the same direction has entered its third
round"*. This direction registered at R622 and has run R623, R624, R626, R651, R652, R655, R656 — seven
working rounds past that threshold. The checkpoint was **not** run when it first fell due; it is run now,
before any further work on the direction, and the lateness is recorded rather than smoothed over. The
consequence of a late checkpoint is stated honestly at the end: it is a process defect, not a reason to
treat the earlier rounds as un-reviewed — every one of them carried its own certificate, and the
corrections they forced are on the record.

## (a) What result would FALSIFY this direction

Each of these would end or re-scope the paper; they are written so that a later round can check them
against the instrument rather than against its own memory.

1. **The design law failing on a natural protocol.** The paper's central claim is: *a protocol's rank is
   faithful to payoff **iff** its score is a strictly increasing function of the policy's **own**
   payoff-profile value; any row-reading aggregation breaks it.* It is measured at **0 mismatches over
   19 protocols × 9 games**, with **0 of 11 row-reading protocols faithful** and exactly two faithful
   designs (`mean_payoff`, `spread`). **Falsifier**: one natural (not constructed) protocol of either
   kind violating the prediction — a row-reading design that reads faithful in every cell, or a
   profile-only design that reads gameable. The `tail_swap` construction is not evidence against the
   law, because it was built to satisfy the law's hypothesis in the band the law predicts.
2. **The gain not being attainable.** `G > 0` in **474/684** cells (79/114), flat across n (50–55 of 76
   on every one of nine rungs), with the monotone control reading **exactly 0**. **Falsifier**: a grid on
   which the divergence collapses — a plausible outcome, since the whole construct could have been a
   definitional tautology.
3. **The protocol not being the lever.** `SS_protocol > SS_population` in **9 of 9** games (MS ratio
   3.9×–48×). **Falsifier**: a game in which a population change moves the ordering more than a protocol
   change does — which would make the paper's lever the ecology, not the protocol.
4. **The ground truth not being exact.** The instrument is the ground truth only because it recovers the
   analytic anchors: `fpsb_n2` at `b(v) = v/2`, `spsb` at the weakly dominant `b(v) = v`, with `cv_n4` a
   **stated absence** (no linear-shading policy is a best response to itself). **Falsifier**: an anchor
   that fails to be recovered, or an anchor asserted without its margin. Two such defects were already
   caught and fixed (the second-price price bug; the `--json` route).
5. **The novelty collapsing to the published phenomenon.** ERPBench (arXiv:2609.04667) already reports
   that winners change across ecologies (21 of 100 problems). **Falsifier**: the paper's content reducing
   to *that phenomenon re-measured* — i.e. the laws disappearing and only the cross-cell count remaining.
   The laws, the nesting, the separation ladder, and the one-design maximal opposition are what keep it
   from being a re-measurement; if a reader can strike them and the paper still stands, this falsifier
   has fired.

## (b) What evidence now exists — and what it does and does NOT support

**Exists, exact, with certificates and byte-identical artefacts:**

| instrument | scope | certificate |
|---|---|---|
| `spike_v0.py` | 4 games × 8 policies × 4 populations × 7 protocols = 112 cells | 23/23 |
| `spike_v1.py` (theory arm) | T1–T4 over the v0 grid | 17/17 |
| `spike_v2.py` (design space) | 17 protocols × 4 games × 4 populations = 272 cells | — |
| `spike_v3.py` (transport) | 272 cells + 408 transport entries | 23/23 |
| `spike_v4.py` (ladder) | 9 games × 8 policies × 4 populations × 19 protocols = **684 cells, 1,026 entries** | 35/35 |
| `census_excess_entries.py` | entry-level re-read of the naive law | 8/8 |
| `census_converse_scope.py` | the converse's two factors | 16/16 |

**Supported by that evidence.**
- **P1 CONFIRMED**: rank is buyable — `G > 0` in 474/684 cells, and the maximum the zoo permits is
  attained by a *real* lower-is-better score (`neg_mean`: `G_max = 7`).
- **P2 CONFIRMED** at every rung: the protocol, not the population, is the lever (9/9 games, exact
  two-way decomposition).
- **P3 REFUTED, with a direction**: "buyable rank and fragile rank are one property" is false —
  fragility is **strictly broader** (564 ⊋ 474, `G > 0 ⇒ tau < 1` with **0 counterexamples**), and the
  two are **maximally opposed on one design** (`rank_score`: gameable in every cell, transport excess
  exactly 0 in every entry).
- **The design law** (19 protocols × 9 games, 0 mismatches) and the **separation ladder**
  (`λ_τ = 1/16 < λ_G = 1/8`: an audit reading the *ordering* fires earlier than one reading the
  *champion*).
- **The naive transport law is refuted at the unit the statistic lives on** — 86 informative violations
  inside the design space of record, over 8 designs, needing no constructed witness.

**NOT supported, and the paper must say so.**
- **No real-world arm.** Every number is from a declared, exactly computable in-silico design space.
  There is no re-read of a published agentic-market leaderboard under a counterfactual population —
  the registered upgradability path (2), not done. By Phase B item 15 (**synthetic data may prove the
  pipeline, never the conclusion**) the claims are scoped to the declared design space and the paper
  states that no claim is made about a deployed benchmark.
- **The transport law's converse is undecidable in this space**, decomposed into two factors: (i) a
  population pair exactly **14/28** apart is **reachable** (certified witness, `spsb_n2/n3/n4`), and
  (ii) a **mixed-oriented protocol is empty everywhere** (19 protocols, none is `+1` in one population
  and `−1` in the other) — with the condition that would supply it **named and demonstrated** (a
  population-conditional score). A bounded negative, not a theorem and not a gap.
- **n ≤ 4, single-round, linear-shading zoo.** `cv_n4`'s anchor absence is a finding about the
  winner's-curse regime, and it bounds where the laws are claimed.
- **Nothing about dynamics**: the population is fixed-weight and the policies do not learn. Upgradability
  path (1) is future work, not evidence.

## The decision

**CONTINUE — to Phase B (submit) at contribution level `theory+empirics`.**

Reason: the evidence pre-assessment does **not** fail. There is a theory model (the corrected
characterization, the dominance `G > 0 ⇒ τ < 1`, the separation ladder, the entry-level orientation
theorem), measured on an exact design space with ground truth by construction, with a two-sided
certificate throughout and a registered prior (P3) that the study **refutes with a direction** — which
is the strongest kind of novel result this journal's bar recognises.

What would change the answer: if falsifier (1) or (5) fired on the manuscript's own numbers — a design
law mismatch on a natural protocol, or the laws dropping out and leaving only the ERPBench phenomenon —
the honest move would be **downgrade to case study** (a protocol-level measurement report), not
continuation.

**Next step named**: Phase B — organize `papers/issue-141/` (manuscript, figures, reference-check.md,
README, one-command reproduction), then submit. The claim boundary above travels into the abstract and
the threats section verbatim in substance.
