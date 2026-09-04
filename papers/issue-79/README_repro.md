# Issue #79 — Reproduction

## One command
    bash reproduce.sh

re-trains the six central cells of the regime table (WALL / RACE seeds 0-2 /
CREATE seeds 0-2 / DESTROY / GREEDY-BLIND) from the persisted SFT bases at
pinned seeds, evaluates at the fixed held-out prompt seed 777, and runs
validate.py which asserts the manuscript's reported numbers with tolerance
+-0.03. Expected exit: 0 with "10/10 checks passed".

## What it runs
- `reproduce.py` — for each cell: load the SFT base checkpoint, run KL-anchored
  GRPO (500 steps for add/parity and count L20; 400 for count L12; n_group=8),
  save the RL checkpoint, evaluate greedy (n=384) and pass@64 (n=48) at eval
  seed 777.
- `validate.py` — asserts the 10 reported numbers (greedy per cell, pass@64 for
  the GREEDY-BLIND cell, and the DESTROY degradation ordering).

## Environment
uv-managed python (3.12 + numpy + torch 2.9.1 CPU). All dependencies in the
existing .venv; the runners import only the local modules (tasks.py, addY.py,
parityY.py, spike_sft.py, spike_rl.py, harness.py).

## Persisted checkpoints (51 total)
ckpts/sft_*_s{0,1,2}.pt and rl_*_s{0,1,2}.pt cover every cell in the manuscript
tables plus the ablation and band runs (R169-R175); reproduce.py re-derives the
RL checkpoints from the SFT bases so the one command verifies end-to-end.

## Runtime note
~40-60 min on 10 CPU cores (each RL cell 100-250 s; the RACE/CREATE cells are
3 seeds each). Full per-round research logs: notes_r163.md .. notes_r175.md.
