#!/usr/bin/env bash
# Issue #63 — one-command reproduction.
# Regenerates the hypotheses report from committed snapshots (no network) and
# runs the independent validation. Exit 0 iff report regenerates byte-identical
# to the canonical snapshot AND validate.py passes.
set -euo pipefail
cd "$(dirname "$0")"

python3 hypotheses.py > /dev/null
if cmp -s snapshots/hypotheses_report.txt snapshots/expected_output/hypotheses_report.txt; then
    echo "OK: hypotheses_report.txt byte-identical to canonical"
else
    echo "FAIL: hypotheses_report.txt differs from canonical" >&2
    diff snapshots/expected_output/hypotheses_report.txt snapshots/hypotheses_report.txt | head -20 >&2
    exit 1
fi

python3 validate.py
echo "== reproduction complete =="
