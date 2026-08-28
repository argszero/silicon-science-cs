#!/bin/bash
# Issue #38 reproduction: offline aggregate -> canonical output.
# Exit 0 iff expected_output/discovery_results.txt regenerates byte-identical.
set -uo pipefail
cd "$(dirname "$0")"

FAILED=0
echo "== offline -> expected_output/discovery_results.txt =="
python3 reproduce.py offline > .out.txt
if diff -q expected_output/discovery_results.txt .out.txt >/dev/null; then
    echo "OK: discovery_results byte-identical"
else
    echo "FAIL: discovery_results deviates" >&2
    diff expected_output/discovery_results.txt .out.txt | head -20 >&2
    FAILED=1
fi
rm -f .out.txt
exit $FAILED
