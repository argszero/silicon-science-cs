#!/usr/bin/env bash
# Issue #65 — eBPF in the Wild: one-command reproduction.
# Offline: regenerates all reports from committed snapshots only (no network,
# no GitHub API). Fails (exit 1) on any byte mismatch or validator failure.
set -u
cd "$(dirname "$0")"
PASS=1

echo "== regenerate reports from committed snapshots =="
python3 classifier_v1.py > /dev/null || { echo "FAIL: classifier_v1.py"; exit 1; }
python3 hypotheses.py  > /dev/null || { echo "FAIL: hypotheses.py";  exit 1; }
python3 sensitivity.py > /dev/null || { echo "FAIL: sensitivity.py"; exit 1; }

echo "== byte-compare against canonical expected output =="
for f in classifier_v1_stats.txt hypotheses_report.txt sensitivity_report.txt; do
  if diff -q "snapshots/$f" "snapshots/expected_output/$f" > /dev/null; then
    echo "  OK: $f byte-identical"
  else
    echo "  MISMATCH: $f"
    diff "snapshots/$f" "snapshots/expected_output/$f" | head -20
    PASS=0
  fi
done

echo "== independent re-count =="
python3 validate.py || PASS=0

echo "== trace check: manuscript numbers -> committed artifacts =="
python3 trace_check.py || PASS=0

if [ "$PASS" -eq 1 ]; then
  echo "== reproduction complete: all byte-identical, 13/13 re-count OK, 0 gaps =="
  exit 0
else
  echo "== reproduction FAILED =="
  exit 1
fi
