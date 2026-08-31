#!/usr/bin/env bash
# Issue #52 — one-command byte-identical reproduction.
# Regenerates the report from committed snapshots and compares against the
# frozen canonical output. Exit 0 iff byte-identical.
set -euo pipefail
cd "$(dirname "$0")"

python3 reproduce.py > /tmp/issue52_report.txt
if cmp -s /tmp/issue52_report.txt expected_output/discovery_results.txt; then
    echo "== offline -> expected_output/discovery_results.txt =="
    echo "OK: discovery_results byte-identical"
    exit 0
else
    echo "FAIL: discovery_results differs from canonical" >&2
    diff expected_output/discovery_results.txt /tmp/issue52_report.txt | head -20 >&2
    exit 1
fi
