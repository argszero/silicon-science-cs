#!/usr/bin/env bash
# One-command reproduction for issue #79 — six central cells of the regime table
# (WALL / RACE seeds 0-2 / CREATE seeds 0-2 / DESTROY / GREEDY-BLIND).
#
# From a FRESH CLONE this is genuinely one command: on first run it bootstraps a
# local .venv (python3 -m venv + pip install torch==2.9.1; needs network once),
# trains any missing SFT base checkpoints into ckpts/, re-trains the RL cells at
# pinned seeds, evaluates at the held-out prompt seed 777, and validates against
# the manuscript regime table with the two-tier scheme of manuscript §8
# (Tier A exact-value cells + Tier B mechanism-level cells).
#
# Usage:  bash reproduce.sh     (CPU-only; ~40-60 min on 10 cores first time)
# Exit 0 iff all Tier A and Tier B checks pass.
set -euo pipefail
cd "$(dirname "$0")"

PY=./.venv/bin/python
if [ ! -x "$PY" ]; then
  echo "== no ./.venv found — bootstrapping (one-time; needs network for the torch wheel) =="
  python3 -m venv .venv
  ./.venv/bin/pip install --quiet "torch==2.9.1"
fi

LOG="$(mktemp -t issue79_repro.XXXXXX.log)"
trap 'rm -f "$LOG"' EXIT

echo "== issue #79 reproduction: six central cells =="
"$PY" reproduce.py 2>&1 | tee "$LOG"
echo ""
echo "== validating: Tier A exact cells + Tier B mechanism cells (see manuscript §8) =="
"$PY" validate.py "$LOG"
echo "REPRODUCTION OK: all checks passed."
