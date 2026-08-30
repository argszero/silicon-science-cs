#!/bin/bash
# Issue #50 reproduction: offline regenerate -> canonical output, byte-identical.
# Exit 0 iff expected_output/signals.json + expected_output/hypotheses.txt
# regenerate byte-identically from the committed raw snapshots.
set -uo pipefail
cd "$(dirname "$0")"

python3 reproduce.py offline
exit $?
