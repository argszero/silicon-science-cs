#!/usr/bin/env bash
# One-command reproduction for issue #20 (offline mode).
# Reads the committed data_snapshot/, recomputes all statistics, and diffs
# against expected_output/manuscript_results.txt. Exit 0 = byte-identical.
set -euo pipefail
cd "$(dirname "$0")"

OUT=".reproduce_check.txt"
trap 'rm -f "$OUT"' EXIT

python3 reproduce.py > "$OUT"
if diff -q expected_output/manuscript_results.txt "$OUT" >/dev/null; then
    echo "OK: output byte-identical to expected_output/manuscript_results.txt"
    exit 0
else
    echo "FAIL: output deviates from expected_output/manuscript_results.txt" >&2
    diff expected_output/manuscript_results.txt "$OUT" | head -40 >&2
    exit 1
fi
