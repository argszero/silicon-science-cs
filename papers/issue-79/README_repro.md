# Issue #79 — Reproduction (internal run/variance inventory)

## One command
    bash reproduce.sh

From a fresh clone: bootstraps `.venv` (python3 -m venv + pip install
torch==2.9.1) on first run, re-trains the central cells (WALL / RACE seeds 0-2 /
CREATE seeds 0-2 / DESTROY / GREEDY-BLIND) from scratch-trained SFT bases at
pinned seeds, evaluates at the fixed held-out prompt seed 777, and validates
with the two-tier scheme of manuscript §8. Expected exit: 0 with
"11/11 checks passed (Tier A exact: 3; Tier B mechanism: 8)".

## Two-tier validation (why not a uniform ±0.03)

The manuscript's stochastic cells vary run-to-run by ~±0.1 at 1.8M-token scale
(GRPO with n_group=8; eval sampling at temp 0.8 is unseeded per draw), so a
uniform ±0.03 "10/10 exact" claim is not honestly reproducible — the editor's
independent clean-clone run reproduced every mechanism but only 5/10 cells
within ±0.03. The scheme therefore distinguishes:

- **Tier A (exact-value, asserted)**: structural cells with no sampling support —
  WALL rl_ca = rl_p64 = 0.000, GREEDY-BLIND rl_odd = 0.000. Identical on every
  independent run to date (3 runs × all seeds of the research phase included).
- **Tier B (mechanism-level, asserted)**: the taxonomy and effect directions
  (RACE seed-lottery, CREATE greedy lift, DESTROY degradation ordering,
  GREEDY-BLIND live-pass@64-at-greedy-0). Robust to ±0.1 stochasticity.
- **Reported, not asserted**: exact stochastic-cell values per run (below).

## Observed stochastic-cell values (greedy metrics, eval seed 777)

| Cell | R177 author run | Editor clean run | R179 clean re-run | Manuscript Table 1 |
|------|-----------------|------------------|--------------------|---------------------|
| RACE L20 s0 rl_g | 0.172 | within ±0.03 of 0.172 | 0.172 | 0.172 |
| RACE L20 s1 rl_g | 0.076 | outside ±0.03 (~±0.1 swing) | 0.174 | 0.076 |
| RACE L20 s2 rl_g | 0.000 | within ±0.03 of 0.000 | 0.003 | 0.000 |
| CREATE L12 s0 rl_g | 0.378 | within ±0.03 of 0.378 | 0.432 | 0.378 |
| CREATE L12 s1 rl_g | 0.505 | outside ±0.03 (~±0.1 swing) | 0.380 | 0.505 |
| CREATE L12 s2 rl_g | 0.565 | outside ±0.03 (~±0.1 swing) | 0.305 | 0.565 |
| DESTROY rl_ca | 0.083 (base 0.156) | outside ±0.03, degrade held | 0.180 (base 0.198) | 0.083 |
| GB rl_p64 | 1.000 (base 1.000) | outside ±0.03 (≥0.9 per mechanism) | **0.021 (base 1.000)** | 1.000 (R175/R177 run) |

The R179 run (2026-09-04, this revision's clean-clone re-verification) shows two
things: (1) mechanism-level reproduction held everywhere — RACE seed-lottery
(two strong seeds this draw), CREATE lifted every seed 5–15x over its base
(R179 bases 0.023–0.065, drawn lower than R169's 0.034–0.130 — same-seed SFT
retraining is not bit-deterministic at this scale, which explains most of the
downstream value spread), DESTROY degraded below base (0.180 < 0.198), and the
three structural zeros reproduced exactly; (2) **GB rl_p64 collapsed to 0.021
while base_p64 stayed 1.000** — the post-RL parity search channel is bimodal
across runs (≈1.0 in R177 + editor run, ≈0 in R179). This is a real finding,
now reported in manuscript §5.5/§8: RL can destroy a perfect 2-value sampling
channel; greedy-only evaluation cannot see it (rl_odd = 0.000 in both modes).

Policy: the three structural cells (Tier A) are asserted exactly; stochastic
values above are reported per run and their spread is stated in manuscript §8 —
readers can distinguish effect from seed lottery via the Tier B directional
checks plus the 3-seed RACE/CREATE structure already in Table 1. GB rl_p64 is
report-only (bimodal, §5.5); GB's asserted mechanism is the *base* channel
(base_p64 ≥ 0.6) plus the Tier A rl_odd = 0.000.

## What the run executes
- `reproduce.py` — per cell: ensure SFT base (train from scratch if absent;
  `os.makedirs` on `ckpts/` so fresh clones work), KL-anchored GRPO (500 steps
  for add/parity and count L20; 400 for count L12; n_group=8), save RL ckpt,
  evaluate greedy (n=384) and pass@64 (n=48) at eval seed 777.
- `validate.py` — two-tier assertions described above; prints the observed
  per-cell values for this run's variance record.

## Environment
python3 -m venv (3.12) + pip torch==2.9.1 (CPU; no numpy needed — no module
imports it). All dependencies from the local `.venv` created by reproduce.sh;
runners import only the local modules (tasks.py, addY.py, parityY.py,
spike_sft.py, spike_rl.py, harness.py).

## Research-phase checkpoints (not committed)
`research/ckpts/` (git-ignored) holds the 51 persisted SFT/RL checkpoints from
R169-R175; reproduce.py regenerates SFT bases on demand, so the one command is
self-contained. Full per-round research logs: notes_r163.md .. notes_r177.md in
`research/`.
