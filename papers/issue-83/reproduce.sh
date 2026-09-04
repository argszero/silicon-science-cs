#!/usr/bin/env bash
# One-command reproduction for issue #83 — recovery result (DESTROY cell).
#
# From a FRESH CLONE this is genuinely one command: on first run it bootstraps a
# local .venv (python3 -m venv + pip install torch==2.9.1; needs network once),
# then trains the c=0.01 SFT base, collapses it with 1500-step GRPO, runs the
# recovery arms (continue / KL-reanchor b=0.01 / KL-reanchor b=1.0 / SFT-replay),
# evaluates at held-out seed 777, and validates with the two-tier scheme of
# manuscript section 8 (Tier A structural + Tier B mechanism).
#
# Usage:  bash reproduce.sh     (CPU-only; ~20-40 min on 10 cores (measured 17 min) first time)
set -euo pipefail
cd "$(dirname "$0")"

PY=./.venv/bin/python
if [ ! -x "$PY" ] || ! "$PY" -c "import torch" 2>/dev/null; then
  echo "== bootstrapping .venv (one-time; needs network for the torch wheel) =="
  if [ ! -x "$PY" ]; then
    python3 -m venv .venv
  else
    echo "== .venv exists but torch is missing — installing into it =="
  fi
  ./.venv/bin/pip install --quiet "torch==2.9.1"
fi

LOG="$(mktemp -t issue83_repro.XXXXXX.log)"
trap 'rm -f "$LOG"' EXIT

echo "== issue #83 reproduction: collapse -> recovery arms =="
"$PY" reproduce.py 2>&1 | tee "$LOG"
echo ""
echo "== validating: Tier A structural + Tier B mechanism (manuscript section 8) =="
"$PY" validate.py "$LOG"
echo "REPRODUCTION OK: all checks passed."
