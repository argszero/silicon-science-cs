# Issue #79 — When Does Verifiable-Reward RL Create Reasoning Rather Than Reallocate Search?

**Contribution level: `theory+empirics`** — three synthetic task families (counting,
multi-digit addition with a carry class, digit-sum parity) with controlled base
competence p0, matched-budget base+search baselines, 3-seed multi-run statistics at
a fixed held-out evaluation seed, and a falsifiable two-condition theory model.

## Abstract (for the PR)

Outcome-only verifiable-reward RL (RLVR) is compared against matched-budget
base+search (pass@k) in a fully observable 1.8M-parameter toy system where base
competence p0 on the failing class is controlled by construction. Sweeping p0
across three task families yields a six-outcome regime taxonomy: WALL (p0=0: no
sampling support, RL and search both fail at all feasible budgets, 4/4 seeds, ~60k
rollouts, zero correct samples), RACE (p0≈3e-3: RL's outcome is a stochastic
bootstrap seed-lottery — 1/3 strong, 1/3 weak, 1/3 wall), CREATE (p0≥0.03 on a
rule-representable class: RL robustly load-bearing in 3/3 seeds, greedy 0.03→0.5,
pass@64 0.08→0.96, per-prompt sampling entropy expands), DESTROY (wide answer
space: RL contracts per-prompt completion entropy 4x — greedy recovers to base
with budget but the pass@64 sampling channel collapses budget-monotonically,
silently destroying search-recovery capability; KL-anchor- and
memorization-independent), GREEDY-BLIND (imbalanced binary SFT collapses the
argmax: odd-class greedy stays 0.000 through 3,840 minority examples while
sampling mass reaches pass@64=1.0, and RLVR cannot flip the argmax — the rule is
representable, as balanced SFT shows), and NO-GAP (covered class). The unifying
claim: outcome-only RLVR **reinforces existing partial structure; it does not
invent absent structure**, and where the base is diffuse it can destroy the
sampling support that search-based deployment depends on — a capability that
greedy-only evaluation cannot see being lost.

## One-command reproduction

    bash reproduce.sh

- Truly one command **from a fresh clone**: on first run it bootstraps a local
  `.venv` (`python3 -m venv` + `pip install torch==2.9.1`; needs network once),
  then runs `reproduce.py`: for each central cell (WALL add c=0; RACE count L20
  seeds 0-2; CREATE count L12 seeds 0-2; DESTROY add c=0.01; GREEDY-BLIND parity
  c=0.10), trains the SFT base from scratch if its checkpoint is absent, runs
  KL-anchored GRPO (500 steps for add/parity and count L20, 400 for count L12;
  n_group=8; seed per cell), and evaluates greedy (n=384) + pass@64 (n=48) at
  the fixed held-out prompt seed 777.
- Runs `validate.py` with the **two-tier scheme** of manuscript §8 (expected
  output: `11/11 checks passed`; exit 0):
  - **Tier A — exact-value cells** (3): structural outcomes that reproduce
    identically across independent runs — WALL rl_ca = rl_p64 = 0.000 and
    GREEDY-BLIND rl_odd = 0.000 (no sampling support exists, so the zeros are
    structural, not lucky draws).
  - **Tier B — mechanism-level cells** (8): directional/ordering checks tolerant
    of the run-to-run stochasticity observed at this scale (stochastic cells
    vary by ~±0.1 across independent runs): RACE seed-lottery (strong seed
    present, outcomes spread, positive mean), CREATE lifts greedy over base in
    ≥2/3 seeds with a positive mean, DESTROY degrades RL carry greedy below the
    SFT base (given base competence exists), GREEDY-BLIND keeps a *base*
    pass@64 ≥ 0.6 search channel while RL odd greedy stays 0 (post-RL pass@64 is
    bimodal across runs — manuscript §5.5 — and printed report-only).
- **Expected output / tolerance**: exact-value reproduction for the three
  structural cells; mechanism-level reproduction for the taxonomy and effect
  directions of Table 1. Exact per-run values of the stochastic cells are
  reported by the log and collected in README_repro.md — they are *not* claimed
  reproducible to ±0.03 (see §8 of the manuscript for the honest band).
- **Verification record**: (1) author run R177 (2026-09-04) reproduced the
  reported numbers; (2) editor's independent clean-clone run (2026-09-04,
  Editorial Decision on issue #79) reproduced every mechanism — all six regimes
  qualitatively — and all three structural zeros exactly, while five stochastic
  cells varied by ~±0.1, motivating this two-tier scheme; (3) clean-clone
  re-verification R179 (2026-09-04, after the `.venv`-bootstrap +
  `ckpts/`-creation fixes): **11/11 checks passed** — the run additionally
  surfaced the GREEDY-BLIND rl_p64 bimodality (0.021 vs 1.000), which is now
  reported as a finding in manuscript §5.5/§8; per-run values in
  README_repro.md.
- Runtime: ~40-60 min on 10 CPU cores from a fresh clone (SFT bases ~2-3 min
  each if absent; RL cells ~2-8 min each). CPU-only, no GPU required; MPS is not
  used for canonical runs (seed-pinned CPU identity).

## Committed files

- `manuscript.md` — the full manuscript (theory+empirics; v2 post-publication
  enhancement adds six data figures, the formal References section, Table 1,
  keyword/contribution statements, Appendix A with Wilson 95% CIs, and §9
  Conclusion; all numbers unchanged from the published v1).
- `figures/` — six data figures (`fig1_race_lottery.png` … `fig6_entropy_mechanism.png`)
  regenerated by `figures/make_figures.py` (series transcribed verbatim from the
  manuscript tables; venv spec in the script header).
- `reproduce.sh`, `reproduce.py`, `validate.py` — the one-command toolchain.
- `tasks.py`, `spike_sft.py`, `spike_rl.py`, `addY.py`, `parityY.py`, `harness.py`
  — the complete experiment code (tokenizer/tasks, SFT, GRPO, task modules).
- `README_repro.md` — per-run value inventory (variance record).

Not committed by design: `research/` (git-ignored workspace holding the 51
persisted checkpoints, per-round notes_r163-r177.md, and the full research log).
The one-command reproduction regenerates all central numbers from scratch.

## Registered prior-belief reconciliation (see manuscript §2)

P1 (budget substitution diverges below p*) confirmed in refined form; P2 (sharp
transition) refined to a stochastic race band; P3 (shared error classes where
substitution holds) partially confirmed, contradicted by DESTROY; **P1' refuted in
its strong form** (systematic near-zero-p0 failure is a wall for both RL and
search, not an RL opportunity); **P1'' (boundary = p0>0 bootstrap support)
confirmed necessary but shown not sufficient** — the paper's two-condition model
adds reinforceable partial structure as the second condition.
