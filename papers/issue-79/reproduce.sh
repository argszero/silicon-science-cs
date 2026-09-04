#!/usr/bin/env bash
# Reproduce the six central cells of issue #79 (WALL/RACE/CREATE/DESTROY/GREEDY-BLIND).
# Re-trains RL from persisted SFT bases at pinned seeds, evaluates at held-out seed 777,
# and validates the manuscript's regime-table numbers with tolerance +-0.03.
#
# Usage:  bash reproduce.sh      (CPU-only; ~40-60 min on 10 cores)
# Exit 0 iff validate.py reports all checks passed.
set -euo pipefail
cd "$(dirname "$0")"

echo "== issue #79 reproduction: six central cells =="
./.venv/bin/python reproduce.py 2>&1 | tee /tmp/issue79_repro.log
echo ""
echo "== validating against manuscript regime table (tol +-0.03) =="
./.venv/bin/python validate.py /tmp/issue79_repro.log
echo "REPRODUCTION OK: all central cells reproduce the manuscript numbers."
