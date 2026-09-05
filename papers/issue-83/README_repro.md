# Issue #83 — Reproduction / per-run value inventory

## One command
    bash reproduce.sh

From a fresh clone: bootstraps .venv (torch 2.9.1), trains the c=0.01 SFT base,
collapses it (1500-step GRPO), runs the recovery arms (continue / KL-re-anchor β=0.01
and 1.0 / SFT-replay 600), validates with the two-tier scheme. Expected exit: 0 with
all Tier A + Tier B checks passed.

## Two-tier validation (why no uniform ±0.03)

The issue #79 R179 lesson applies unchanged: stochastic cells vary run-to-run by
~±0.1 at 1.8M-token scale (GRPO n_group=8; eval sampling unseeded per draw), so a
uniform exact-value claim is not honestly reproducible. Scheme: Tier A asserts only
structural signatures (collapsed greedy-recovered/channel-collapsed); Tier B asserts
mechanism directions (replay ≥ base, policy-space arms < base − 0.3). Exact stochastic
values are reported per run below.

## Author-run observed values (R182–R184, eval seed 777, add c=0.01 seed 0 unless noted)

| Cell | value | note |
|---|---|---|
| base s0 pass@64 | 0.792–0.875 | across evals (n=48 noise ~±0.08) |
| collapsed s0 (1500 RL) pass@64 | 0.146 | greedy 0.161 ≈ base 0.156 |
| continue 500 / 1000 | 0.271 / 0.188 | plateau |
| KL-re-anchor β=0.01 500 | 0.104 | worse than start |
| KL-re-anchor β=0.1 500 | 0.146 | flat |
| KL-re-anchor β=1.0 500 / 1000 | 0.312 / 0.333 | partial plateau |
| entropy bonus λ=0.005 500 | ~0.19 | inert |
| entropy bonus λ=0.02 / 0.05 500 | 0.000 | format destroyed |
| **SFT-replay 600 (s0)** | **0.938** | ≥ base; @300 = 0.729, @450 = 0.854 |
| base s1 / collapsed s1 / replay s1 | 0.292 / 0.208 / **0.854** | replay 2.9× base |
| base s2 / collapsed s2 / replay s2 | 0.417 / 0.062 / **0.438** | replay ≥ base |
| parity base / collapsed / replay (odd p64) | 0.958 / ~0.02 / **0.938** | greedy 0.000 all three |
| fresh SFT @300 (warm-start control) | 0.000 | carry not bootstrapped |

## Entropy mechanism (16 fresh carry prompts × 64 samples, temp 0.8)

| checkpoint | entropy bits | distinct/prompt |
|---|---|---|
| base | 2.51 | 10.81 |
| collapsed | 0.50 | 3.00 |
| replay 600 | 2.66 | 9.19 |
| strong-KL β=1 | 0.77 | 3.69 |

Note: per-sample correct probability ~0 for all in this 16-prompt draw (carry correct
answers concentrate on the sum island 110–119, rarely drawn) — entropy is the
within-draw discriminator; pass@64 (n=48) is the correctness metric.

## Research-phase artifacts (not committed)
`research/` holds notes_r182..r184.md, the recovery runners (recover_rl.py,
parity_recover.py, diag_ent_rec.py), and the persisted checkpoints (rec_*), plus the
symlinked issue-79 modules/checkpoints they build on. reproduce.py regenerates the
central add-cell result from scratch; the parity subject is the issue-79 R179
clean-clone checkpoint (bimodal collapse; single available destroyed draw).
