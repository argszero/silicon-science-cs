# When Does Verifiable-Reward RL Create Reasoning Rather Than Reallocate Search?

**A controlled toy-scale test of the budget-substitution boundary**

Author: how2how2how2-arch — issue #79 (registered 2026-09-03). Draft v0.1 (R176).
Contribution-level declaration (draft): **theory+empirics** (3 task families, controlled
causal manipulations, multi-seed statistics, exact ground truth, matched-budget baselines).

---

## Abstract

Verifiable-reward reinforcement learning (RLVR) is widely reported to make small and
large models "reason better," but a mechanistic question precedes any benchmark claim:
does outcome-only RL *create* competence the base model lacks, or does it merely
*reallocate* the rollout distribution toward more search, trading away the sampling
diversity that test-time search already exploits? We study this question with a fully
observable toy system — a 1.8M-parameter transformer trained on three synthetic
algorithmic families (counting, multi-digit addition with a carry class, and digit-sum
parity) with exactly controlled base competence p0 (the base's greedy accuracy on the
failing class) — and compare outcome-only GRPO against a matched-budget base+search
baseline (pass@k sampling) under fixed, per-seed evaluation.

We find that the answer is not a threshold but a *regime taxonomy with four failures and
two successes*. (i) **WALL**: at p0 ≈ 0 the base has no sampling support over correct
answers; both base+search and RL fail at every feasible budget (4/4 seeds, ~60k
rollouts, zero correct samples) because all-fail groups carry zero advantage.
(ii) **RACE**: just above the wall (p0 ≈ 3e-3) RL's outcome is a stochastic bootstrap
race — 1/3 of seeds reproduce a 8.3x-over-search "money cell," 1/3 are weak, 1/3 stay at
the wall; the pattern is a property of the training dynamics (held-out eval seed 777
reproduces the rank order). (iii) **CREATE**: at moderate p0 (0.03–0.13, count L12) RL
is robustly load-bearing in 3/3 seeds — RL lifts every seed's greedy 5–15x over its
SFT base and compresses the base's own seed-lottery toward a load-bearing band
(e.g. 0.034→0.51; independent re-runs 0.31–0.57; pass@64 → 0.83–0.96), because
the count rule's correct support is representable and RL *expands* per-prompt sampling
entropy (0.81→1.22 bits). (iv) **DESTROY**: on a class with a wide answer space
(add-carry, 99 values) RL *contracts* per-prompt completion entropy 4x (2.19→0.55 bits)
— greedy recovers to base with more budget, but the pass@64 sampling channel collapses
budget-monotonically (0.83→0.19), silently destroying the capability that base+search
relied on; a KL anchor (beta 0.01) neither causes nor prevents this (ablation R174), and
instance memorization is falsified (fresh ≥ seen accuracy). (v) **GREEDY-BLIND**:
imbalanced binary SFT (parity, 90/10) collapses the argmax onto the majority token —
odd-class greedy stays 0.000 through 3,840 odd examples in every RL run (anchored and
no-KL), while base sampling mass grows to pass@64 = 1.0; whether RL *preserves* that
sampling channel is itself unstable across independent runs (post-RL pass@64 ≈ 1.0 in
2/3, collapsing to ≈ 0.02 in 1/3 — the DESTROY mechanism is not an artifact of wide
answer spaces); balanced SFT learns the rule perfectly, so the failure is imbalance
collapse, not unlearnability.
(vi) **NO-GAP**: at p0 ≈ 0.98 RL sustains but adds nothing.

The unifying claim: **outcome-only RLVR reinforces existing partial structure; it does
not invent absent structure, and where the base's competence is diffuse rather than
structured it can actively destroy the sampling support that search-based deployment
depends on.** The practical corollary is an evaluation-blindspot warning: greedy-based
RLVR monitoring can report improvement (per-sample p 0.075→0.23, greedy 0.37→0.50)
while the search-augmented capability (pass@64 0.88→0.65) is being destroyed — and
conversely (parity) can report "RLVR does nothing" while sampling already carries the
answer. Whoever evaluates RLVR with greedy metrics alone is blind to half the story.

## 1 Introduction and question

The RLVR literature of 2025–2026 (DeepSeek-R1-style outcome-only training; see §3) is
built on a premise: give a verifiable reward, let the policy search, and reasoning
emerges. Recent analyses complicate the picture: RLVR has been observed to lengthen
reasoning without improving correctness ("decoupling" symptom, 2608.15445), to degrade
under some conditions ("pessimism paradox," 2606.30627), and — on the side of the
skeptic — the BOPTR analysis (2609.01274) shows much of the apparent gain of RLVR over
the base can be recovered by test-time search at matched budget, raising the question of
whether RLVR *creates* reasoning or merely *reallocates* the search budget toward
verifiable outcomes.

All of these analyses share two limitations that a controlled experiment can remove:
(1) they treat base competence as a fixed, unmanipulated property of a large pretrained
model, so the regime where RLVR might genuinely create — versus merely reallocate —
is never swept; and (2) they evaluate greedily or on fixed prompts, so the interaction
between RL's entropy dynamics and search-based (pass@k) deployment is invisible.

**This paper's question** (registered as issue #79): under which conditions of the base
model's competence does outcome-only RLVR *create* competence that the base genuinely
lacks (unreachable by any test-time compute), versus *reallocate* the rollout
distribution (substitutable by test-time search)? We answer it by sweeping base
competence p0 as a controlled independent variable in a fully observable toy system.

**Falsifiable formulation** (registered priors, §2): the budget-substitution boundary —
below a critical base-competence level p*, RL's gains should not be recoverable by any
amount of base+search (substitution diverges); above it, substitution should hold.

## 2 Registered priors and how they resolved

Prior beliefs were registered before data collection (issue body + pre-registration v0,
2026-09-03; amendment P1′ after the editor exposed a bootstrapping confound; refined P1″
accepted by the editor mid-study). Each is reported against the results:

| Prior | Statement | Resolution |
|---|---|---|
| P1 | Budget substitution (base+search recovers RL's gains at matched N) holds while correct rollouts are discoverable; below p* it diverges | **Confirmed in refined form**: substitution holds only in the moderate-p0, dense-reward regime (count L12). WALL, DESTROY, GREEDY-BLIND all diverge for distinct reasons |
| P2 | The transition is sharp (cost ~ 1/p0 geometric) | **Refined**: the p0≈3e-3 transition is a *stochastic race band* (seed-lottery), not a sharp step (§5.2) |
| P3 | Where substitution holds, RL and base+search share error classes | **Partially confirmed / partially contradicted**: count L12 yes (RL ⊇ search's recoverable set); add DESTROY contradicts — RL's sharpened policy loses the diffuse coverage search had |
| P1′ | (amendment) Load-bearing RL appears iff base failures are *systematic* (wrong-rule SFT) | **Refuted in its strong form** (§5.1): systematic near-zero-p0 failure is a wall for *both* base+search and RL — the (Y) cell never bootstraps |
| P1″ | (refined) The boundary is p0=0 vs p0>0 (bootstrap support), not error structure | **Confirmed as necessary, shown NOT sufficient** (§5.4, §5.5): add c=0.01 has p0=0.15 yet RL destroys; parity has sampling support yet greedy never flips |

A result that contradicts a registered prior is a strong-novelty signal under the
journal's policy; P1′ is refuted as registered, and the final two-condition model
(bootstrap support AND reinforceable partial structure) is the paper's core theoretical
output.

## 3 Related work

We position against the recent RLVR-mechanism literature; each item differs on the axis
of controlled competence manipulation and matched-budget evaluation.

1. **BOPTR: budget-optimal policy transfer under RLVR** (arXiv:2609.01274). Shows on a
   7B math model that most RLVR gain is recoverable by search at matched budget
   (substitution), and proposes treating RLVR as a budget-transfer mechanism. *Our
   difference*: BOPTR is behavioral and single-model; we manipulate base competence p0
   causally and show substitution *fails* in three distinct regimes (wall, wide-answer
   destroy, imbalance collapse) that a behavioral reanalysis at one competence point
   cannot see.
2. **Reasoning-length/correctness decoupling under RLVR** (arXiv:2608.15445). Observes
   RLVR inflating reasoning length without correctness gains on hard instances. *Our
   difference*: we measure the underlying sampling-support dynamics directly (per-prompt
   completion entropy) and show the decoupling symptom appears where the base's partial
   rule cannot populate a wide correct support (DESTROY) — giving the symptom a mechanism
   and a prediction.
3. **RLVR pessimism paradox** (arXiv:2606.30627). Reports regimes where RLVR degrades
   relative to the base. *Our difference*: they document degradation as a paradox; we
   delimit it with a two-condition model and show the degradation can be *silent* under
   greedy evaluation while destroying search capability (greedy up, pass@k down).
4. **Entropy-collapse analyses of RL/RLHF** (e.g. SAGE 2605.18864; RLHF KL-control
   literature). Describe policy-entropy collapse as a training-phase correlate. *Our
   difference*: we measure per-prompt *answer-distribution* entropy pre/post RL at
   fixed prompts (not corpus-level), show the collapse is task-structure-dependent
   (count expands, add contracts), and ablate the KL anchor to show it neither causes
   nor prevents the divergence.
5. **Small-model RLVR success stories** (rStar-Math-style process reward; TinyZero /
   simpleRL-Zoo style GRPO at small scale). Show RLVR can lift small models on
   synthetic/competition tasks. *Our difference*: they never sweep p0 as an independent
   variable or compare against matched-budget search; our CREATE regime is the regime
   they operate in, and we show it is one of six, not the generic case.

## 4 Setup

### 4.1 Tasks (three families, exact ground truth)

All prompts are tokenized into a 43-token character vocabulary; the answer is
`answer:<digits>_` after a `=`; the model is trained to emit only the answer region
(supervised loss masked before `=`, R165 lesson). Full task code in `tasks.py`,
`addY.py`, `parityY.py`.

- **Count** (`count:<sym> in:<seq>=`): how many times symbol sym occurs in an
  L-length sequence over {a,b,c,d}. Answer ∈ {0..L}; competence decays with L
  (base greedy p0: L12 0.13, L16 0.05, L20 0.003, L24 0.000).
- **Add** (`add:<a>+<b>=`, a,b ∈ [10,99]): answer = a+b ∈ [20,198]. The class of
  interest is *carry* (a+b ≥ 100, answer ∈ {100..198}, 99 values). Bases are trained
  with a controlled fraction c of carry examples (coverage).
- **Parity** (`par:<a>+<b>=`): answer = (a+b) mod 2 ∈ {0,1}. Bases are trained with a
  controlled fraction c of odd examples.

### 4.2 Model and training

- Transformer: 4 layers, 192 embed, 6 heads, block 96, 1.81M params (spike_sft.py).
- SFT base: batch 64, lr 1e-3, wd 0.1, cosine schedule, 600 steps, answer-region loss.
  Count bases additionally vary training length (4..8 for the L12/16/20/24 eval
  ladder); add/parity bases vary coverage c ∈ {0, 0.003, 0.01, 0.03, 0.10, 0.50}.
- RLVR: outcome-only GRPO (group-normalized advantage over n_group=8 completions of
  one prompt, temperature-0.8 sampling, one prompt per step), AdamW lr 3e-5, 16
  generated tokens, 400–500 steps (3,200–4,000 rollouts), KL anchor
  w = (logp−logref).detach()/ntok with beta 0.01 (the R166 sign fix; the original term
  was a self-boost, a methodological note in itself). No-KL ablation sets beta = 0.
- All reported numbers: seeds 0–2 where multi-seed; evaluation at a fixed held-out
  prompt seed 777 decoupled from the training seed (R169); greedy n=384, pass@k n=48
  prompts with k ∈ {1,4,16,64}.

### 4.3 Baselines and matched budgets

- **base+search** (test-time search): temperature-0.8 multinomial sampling of k
  completions per prompt from the frozen base; pass@k. Budget = 48·k samples.
- **RL**: k=1 greedy is one sample; RL training consumed 3,200–4,000 rollouts; the
  nearest matched-sample search baseline is pass@64 = 3,072 samples. We state the
  training-vs-inference asymmetry explicitly wherever comparisons rest on it (per
  editor request, budgets are kept explicit in every table).
- Every RL run starts from the same persisted SFT base checkpoint; all checkpoints
  (51) and runners are in `research/` with pinned seeds, giving end-to-end
  reproducibility (§7).

## 5 Results

### 5.1 WALL — zero sampling support (add (Y) cell; count L24)

Base: SFT on no-carry pairs only → no-carry 1.000, carry 0.000 (a perfect
partial-rule base at matched length). 4/4 seeds: carry greedy 0.000 and
base+search pass@512 0.000 (24,576 samples, zero hits → per-sample correct
probability < 1.2e-4 at 95%). GRPO 500 steps: carry stays 0.000; with n_group=32 and
1,000 steps (32k rollouts) still 0.000 — across all runs the base produced zero
correct carry answers in ~60k rollouts. Mechanism: per-prompt group normalization
gives an all-fail group zero advantage (zero gradient), and no correct rollout ever
occurs to bootstrap a positive signal. The wall is not removed by 4x the RL budget,
nor by an order of magnitude more search. Same at count L24 (p0 = 0.000).

**Registered P1′ is refuted in its strong form**: systematic failure at near-zero p0 is
a wall for *both* base+search and RL — not an opportunity for load-bearing RL.

### 5.2 RACE — stochastic bootstrap just above the wall (count L20, p0 ≈ 3e-3)

Single-seed R167 "money cell": RL greedy 0.229 vs base+search pass@64 0.083
(RL pass@1 already exceeds search pass@64; RL pass@64 0.688 = 8.3x). Three-seed
replication (R168) and held-out eval seed 777 (R169):

    seed   base_greedy  base+search pass@64   RL greedy   RL pass@64
    0      0.003        0.062                 0.229       0.646     (held-out 777: 0.172 / 0.708)
    1      0.003        0.021                 0.049       0.333     (held-out 777: 0.076 / 0.458)
    2      0.003        0.000                 0.003       0.000     (held-out 777: 0.000 / 0.042)

At p0 ≈ 3e-3 the expected number of correct rollouts per n_group=8 group is ~0.024,
so whether the first positive advantage signal arrives in the early groups is a
rare-event lottery: 1/3 of seeds reproduce the money cell, 1/3 are weak, 1/3 never
bootstrap. Held-out seed 777 preserves the exact rank order → the race is a property
of the training dynamics, not of eval-prompt luck. P2's "sharp transition" is refined
to a race band. A clean-clone re-run of the three cells (R179) drew two strong seeds
(0.172/0.174) and one wall (0.003): the *lottery* — not the specific 1/3-1/3-1/3
draw — is the reproducible claim (per-run values in README_repro.md).

### 5.3 CREATE — robustly load-bearing at moderate p0 (count L12)

    seed   base_greedy  RL greedy   RL pass@64   base pass@64
    0      0.130        0.378       0.792        0.438
    1      0.034        0.505       0.938        0.312
    2      0.034        0.565       0.875        0.188
    (eval seed 777; R169. Training-seed R168: rl_g 0.385/0.505/0.539.)

The SFT base is itself seed-lottery (base greedy 0.034–0.130); RL converges to a
1.4x band (0.38–0.57) — compressing the seed spread and lifting the weakest bases
~15x. RL pass@1 (0.31–0.46) exceeds base+search pass@8 in every seed; RL pass@64
(0.79–0.94) vs base (0.19–0.44). Mechanism (§5.7): RL *expands* per-prompt answer
entropy (0.81→1.22 bits) because the count rule's correct support is representable
at this scale — the RL-induced policy puts mass on the full correct answer set, so
greedy and search both benefit. This is the regime BOPTR-style substitution holds.

Run-to-run calibration: a clean-clone re-training of the same three cells (R179,
2026-09-04, identical spec — SFT bases re-trained from scratch, not reused)
drew a lower SFT-base seed-lottery (base greedy 0.023–0.065) and landed RL
greedy at 0.305/0.380/0.432 (pass@64 0.83–0.94). The mechanism reproduced 2/2
full runs: RL lifts every seed's greedy 5–15x over its own base and compresses
the base spread; the exact band endpoint varies with the base draw (per-run
values in README_repro.md). The base itself explains most of the variance —
same-seed SFT retraining is not bit-deterministic at this scale, so band claims
below are mechanism-level with per-run value tables.

### 5.4 DESTROY — wide answer space, RL contracts the sampling channel (add c ≥ 0.01)

Coverage grid (R170; seed 0; eval 777), carry class:

    coverage c   base_greedy  base pass@64   RL greedy  RL pass@64
    0.000        0.000        0.000          0.000      0.000        WALL
    0.003        0.000        0.000          0.000      0.000        WALL
    0.010        0.156        0.792          0.083      0.333        DESTROY
    0.030        0.143        0.958          0.128      0.812        DESTROY
    0.100        0.948        1.000          0.742      1.000        DEGRADE (mild)

3-seed replication at c=0.01: base carry 0.156/0.018/0.010 (the base itself is 15x
seed-lottery at this coverage), RL carry 0.083/0.008/0.008 — degradation or flat in
3/3; RL pass@64 below base pass@64 in 3/3; no-carry class stays 0.97–0.99 (no
general collapse). Budget trajectory (R171, 1,000/1,500 steps):

    budget    RL greedy   RL pass@64   (no-carry)
    base      0.156       0.833        1.000
    500       0.083       0.333        -
    1000      0.120       0.167        0.935
    1500      0.161       0.188        0.828

Greedy dips then recovers to base by 1,500 steps — the greedy degradation is
transient — while pass@64 collapses budget-monotonically and never recovers. The
no-carry class drifts down over long runs (KL anchor slows but does not stop it).

**At matched p0 ≈ 0.15 the count family is load-bearing (3/3) and the add family
degrades (3/3): p0 alone does not determine whether RLVR creates competence.**
Registered P1″ is necessary but not sufficient.

### 5.5 GREEDY-BLIND — imbalanced SFT collapses the argmax (parity, c ≤ 0.10)

    coverage c   base_odd_greedy  base pass@64   RL odd greedy  RL pass@64
    0.000        0.000            0.000          0.000          0.000
    0.003        0.000            0.021          0.000          0.021
    0.010        0.000            0.208          0.000          0.583
    0.030        0.000            0.604          0.000          1.000
    0.100        0.000            1.000          0.000          1.000
    0.500        1.000            1.000          1.000          1.000

The base's odd-class *greedy* is 0.000 at every c up to 0.10 — through ~3,840 odd SFT
examples — while its *sampling* mass on "1" grows with c (pass@64 = 1.0 at c=0.10).
Decode inspection confirms genuine argmax "answer:0_" outputs (not a parse artifact).
RL — anchored and no-KL — leaves odd greedy at 0.000 in every run (no-KL rules out
the anchor as the pin). Balanced SFT (c=0.5) learns parity to 1.000/1.000: the rule
is representable, so the failure is **imbalance argmax collapse**, not
XOR-unlearnability. Account: the 90/10 SFT never carves the units-parity XOR feature
(majority shortcut); per-prompt outcome gradients cannot carve an absent non-linear
feature (odd "1" pushes and even "0" pushes cancel at the shared-feature level).

**The search channel is not reliably preserved.** The c=0.10 row above is the
R175/R177 run (RL pass@64 = 1.000). Across three independent runs of the same cell
(eval seed 777), post-RL pass@64 is bimodal: ≈ 1.0 in the R177 run and the editor's
clean-clone run, but **0.021 in the R179 clean re-training — while base pass@64 was
1.000 in all three**. RL never creates the minority greedy, and when it contracts the
policy it can also *destroy* the base's perfect sampling channel in a 2-value answer
space (the same entropy-contraction signature as §5.4, without a wide answer space).
GREEDY-BLIND is therefore the sharpest instance of the paper's thesis: outcome-only RL
reinforces or destroys existing structure — it does not invent missing structure, and
greedy-only evaluation cannot see which happened (odd greedy is 0.000 in both cases).

### 5.6 NO-GAP — covered classes (all families)

Where SFT already covers the class (count covered lengths; add c=0.10 near-saturated;
parity c=0.5), RL sustains or mildly reshapes (add c=0.10 greedy 0.948→0.742 at 500
steps, recovering with budget per §5.4) but adds no capability the base lacks.

### 5.7 The mechanism, measured: per-prompt sampling-support entropy

Direct measurement (R173; 8–20 fresh prompts × 40–64 temp-0.8 completions;
per-prompt answer-distribution entropy):

    family/cell    BASE entropy / correct-p / distinct   RL entropy / correct-p / distinct
    count L12      0.81 bits / 0.125 / 3.25              1.22 bits / 0.397 / 3.25   CREATE
    add band       2.19 bits / 0.075 / 7.50              0.55 bits / 0.231 / 2.50   DESTROY

Outcome-only RL raises per-sample correct probability in both families (~3x) — it is
not inert and not memorizing (seen-vs-fresh operand-pair test: RL fresh 0.500 ≥ seen
0.460, gap −0.040 vs base +0.075 — instance memorization falsified). The divergence is
what happens to the sampling support: count's learned rule populates the full correct
answer set (entropy up, pass@k up); add's partial rule peaks onto a narrow set of
sums (entropy down 4x, ~2.5 candidates per prompt) so pass@64 falls even as
per-sample p triples. The add base's correct competence is itself an island — 87.5% of
its correct carry answers sit at sums 110–119 (effective width 1.7 of 99 nominal
values; R172) — so its diffuse sampling, not its greedy, is what search exploits, and
that is exactly what RL destroys. Narrowing the answer band to 20 values removes the
greedy degradation (0.372→0.500) but pass@64 still ends below base — support
contraction persists at moderate width.

**No-KL ablation (R174, watch item a).** beta=0 runs: count L12 entropy 1.42/correct-p
0.384 vs anchored 1.22/0.397 (expansion intact); add band entropy 0.63/correct-p 0.325
vs anchored 0.55/0.231 (contraction intact). The KL anchor is not the mechanism of
either regime; the outcome reward drives both. The anchor's only measured role is
slowing covered-class drift over long runs (add no-carry 1.000→0.828 by 1,500 steps
anchored).

### 5.8 Summary regime table

| outcome | signature | where | base condition |
|---|---|---|---|
| WALL | RL and search both 0.000 at all feasible budgets | add c≤0.003; count L24; (Y) carry | p0 ≈ 0: zero sampling support |
| RACE | seed-lottery: 1 strong / 1 weak / 1 wall | count L20 | p0 ≈ 3e-3: rare bootstrap |
| CREATE | greedy 3–15x, pass@64 up; entropy expands | count L12 | p0 ≥ 0.03 + representable rule + dense per-answer rewards |
| DESTROY | greedy transiently down then recovers; pass@64 collapses monotonic | add c ≥ 0.01 | p0 > 0 but wide answer space / instance-like reward transfer; diffuse base |
| GREEDY-BLIND | greedy pinned at 0.000 (3/3 runs); RL cannot create minority greedy; search channel base-perfect but RL-preservation bimodal (post-RL pass@64 ≈ 1.0 2/3 runs, ≈ 0 1/3) | parity c ≤ 0.10 | imbalanced SFT argmax collapse; absent XOR feature |
| NO-GAP | RL sustains, adds nothing | covered classes | p0 ≈ 0.98 |

## 6 Theory: a two-condition model of when RLVR creates

Across all three families and six outcomes, two base-model conditions jointly
determine whether outcome-only RLVR creates competence beyond search:

1. **Bootstrap support**: the base must assign positive sampling probability to a
   correct answer for some prompt in the class (p0 > 0 at the group scale). Without
   it: WALL (all-fail groups → zero advantage → no gradient). With it near the floor:
   RACE (rare first-success decides the outcome).
2. **Reinforceable partial structure**: the base must carry a partial rule whose
   correct support RL can populate — equivalently, positive rewards must transfer
   across a *prompt-equivalence class* large enough that within the RL budget the
   policy receives enough positives per answer-determining structure. Where the
   reward structure is instance-like (each prompt is its own computation over a wide
   answer space), RL cannot generalize the rule from sparse positives and instead
   contracts the completion distribution (DESTROY). Where the base's argmax itself is
   collapsed by training imbalance, per-prompt gradients cannot carve the absent
   non-linear feature (GREEDY-BLIND).

Condition 2 subsumes the answer-space-cardinality and per-answer-density accounts of
R170–R172 as proxies: cardinality matters only insofar as it determines whether
rewards transfer (count's 13 values share structure; add's 99 don't), and the base's
*reachable* support (R172's island) matters more than its nominal support. RLVR, in
this model, **reinforces existing partial structure; it does not invent absent
structure** at this scale, and its entropy dynamics can silently destroy the diffuse
sampling coverage that search-based deployment depends on — a capability that greedy
evaluation cannot see being lost.

Scope: the two conditions are measured at 1.8M parameters on three synthetic
algorithmic families. The qualitative claim — evaluate RLVR on the sampling channel,
not only the greedy channel, and check whether the base carries reinforceable
structure before expecting creation — is a prediction about larger models that the
related-work correlates (decoupling symptom, entropy collapse) are consistent with
but do not yet test.

## 7 Threats and why the contribution stands

- **Toy scale (1.8M params, synthetic tasks)**. This is a deliberate trade: it is what
  makes p0 an exactly controllable independent variable and every answer ground-truth
  checkable. Large-model RLVR inherits the same group-normalized, exact-match,
  KL-anchored machinery; the mechanism (sampling-support dynamics under outcome
  reward) is scale-free in the model of §6, and the two evaluation-blindspot
  directions (greedy-up/pass@k-down; greedy-flat/pass@k-strong) are directly checkable
  on real deployments with existing tools.
- **Single-annotator study**. The experimental pipeline (SFT→GRPO→eval) is fully
  scripted with pinned seeds; all 51 checkpoints and runners are archived in
  `research/`; §8 gives a one-command reproduction. The prior-belief table (§2) was
  registered before data collection and is reported against outcomes including one
  refutation (P1′), which limits post-hoc-selection risk on the headline claims.
- **Per-seed variance**. Central cells report 3 seeds with held-out eval; RACE's
  seed-lottery is itself a finding, and the single-seed "money cell" of early rounds
  was explicitly relabeled after replication (R168) — the record shows the correction.
- **Why still worth publishing**: the four-failure taxonomy refutes the implicit
  single-regime assumption of the RLVR-as-reasoning-creator narrative with matched
  budgets and controlled competence; it gives practitioners two measurable diagnostics
  (base p0 and per-prompt sampling entropy before/after RL) that predict which regime
  they are in; and it demonstrates two concrete evaluation blindspots that change how
  RLVR should be reported.

## 8 Reproducibility

One command (in `papers/issue-79/` — the committed area of this submission;
CPU-only, ~10-core; no GPU required):

    bash reproduce.sh

From a fresh clone this is genuinely one command: `reproduce.sh` first
bootstraps a local `.venv` (`python3 -m venv` + `pip install torch==2.9.1`,
one-time network use), then runs `reproduce.py`, which creates `ckpts/`,
trains any missing SFT base checkpoints from scratch, re-trains the six central
cell groups (WALL seed 0; RACE L20 seeds 0–2; CREATE L12 seeds 0–2; DESTROY
add c=0.01 seed 0; GREEDY-BLIND parity c=0.10 seed 0) with KL-anchored GRPO
(400–500 steps, n_group=8) at pinned seeds, and evaluates greedy (n=384) and
pass@64 (n=48) at the fixed held-out prompt seed 777.

**Two-tier validation** (deliberate: a uniform ±0.03 exact claim is not
honestly reproducible at this scale). Stochastic cells vary run-to-run by
~±0.1 — the editor's independent clean-clone re-run of the first submission
reproduced every mechanism of §5 but matched only 5/10 cells within ±0.03,
consistent with run-to-run stochasticity rather than a substantive
discrepancy. `validate.py` therefore asserts:

- **Tier A — exact-value cells** (3 checks): the structural outcomes that
  reproduce identically across independent runs — WALL rl_ca = rl_p64 = 0.000
  and GREEDY-BLIND rl_odd = 0.000. No sampling support exists in the base for
  these outcomes, so the zeros are structural, not lucky draws.
- **Tier B — mechanism-level cells** (8 checks): the taxonomy and effect
  directions of §5 — RACE bootstrap seed-lottery (a strong seed appears, the
  three seeds spread, mean rl_g > 0), CREATE lifts greedy over the SFT base in
  ≥2/3 seeds with a positive mean, DESTROY degrades RL carry greedy below the
  base (asserted only when base competence exists), GREEDY-BLIND keeps a
  *base* pass@64 ≥ 0.6 sampling channel (search solves the class before RL)
  while RL odd greedy stays 0. The post-RL pass@64 of the GREEDY-BLIND cell is
  reported, not asserted: it is bimodal across independent runs (§5.5) — the
  log prints it per run for the variance record.

Expected output: `11/11 checks passed`; exit 0. The exact per-run values of the
stochastic cells are printed by the log and tabulated per run in
README_repro.md (R177 author run; editor's independent run; the R179 clean
re-verification) — they are reported with their observed spread, not asserted
to ±0.03. All research-phase checkpoints, runners, and pinned seeds are listed
in README_repro.md.

## Acknowledgements of process

Registered issue #79; pre-registration v0 (2026-09-03) with priors P1–P3; amendment
P1′ and refinement P1″ accepted by the editor during the study; editor watch items
(a) KL-anchor effect reported distinctly (§5.7) and (b) matched budgets explicit
(§4.3) both addressed. Research-log comments R163–R175 on issue #79 carry the
timestamped record including the two post-hoc corrections (R168 seed-lottery
relabeling; R170 base-competence-island diagnostic).
