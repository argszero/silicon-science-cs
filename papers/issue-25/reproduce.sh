#!/usr/bin/env bash
# One-command reproduction for issue #25 (offline mode).
# Reads the committed data_snapshot/, recomputes all statistics (C1/C2 via
# reproduce.py, C3 via c3_classify.py), and diffs against the frozen expected
# outputs. Exit 0 = byte-identical.
set -euo pipefail
cd "$(dirname "$0")"

OK=1
python3 reproduce.py > .out_discovery.txt
if diff -q expected_output/discovery_results.txt .out_discovery.txt >/dev/null; then
    echo "OK: discovery_results byte-identical"
else
    echo "FAIL: discovery_results deviates" >&2
    diff expected_output/discovery_results.txt .out_discovery.txt | head -20 >&2
    OK=0
fi
python3 c3_classify.py > .out_c3.txt
if diff -q expected_output/c3_results.txt .out_c3.txt >/dev/null; then
    echo "OK: c3_results byte-identical"
else
    echo "FAIL: c3_results deviates" >&2
    diff expected_output/c3_results.txt .out_c3.txt | head -20 >&2
    OK=0
fi
rm -f .out_discovery.txt .out_c3.txt
exit $OK
