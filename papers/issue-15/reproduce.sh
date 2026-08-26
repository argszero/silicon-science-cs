#!/usr/bin/env bash
# One-command reproduction — issue #15 "Conventional Commits in the Wild".
#
#   bash reproduce.sh
#
# Runs the canonical analyzer in OFFLINE mode over the committed data
# snapshot (data_snapshot/) and diffs the fresh output against
# expected_output/manuscript_results.txt — exit 0 iff byte-identical.
#
# The data snapshot was fetched from the GitHub REST API (gh auth) on
# 2026-08-26 at the pinned corpus; --offline guarantees byte-identical
# reproduction without network access. To refresh the data instead:
#   python3 reproduce.py            # online fetch (needs gh auth)
#   python3 reproduce.py --offline  # analyze snapshot
#
# Requires: bash, python3 >= 3.10 (stdlib only).
set -euo pipefail
cd "$(dirname "$0")"

OUT_TMP=".repro_out.txt"
python3 reproduce.py --offline > "$OUT_TMP" 2>/dev/null

if diff -u expected_output/manuscript_results.txt "$OUT_TMP"; then
  echo "REPRODUCTION OK: fresh offline output identical to expected_output/manuscript_results.txt"
  rm -f "$OUT_TMP"
else
  echo "REPRODUCTION MISMATCH — fresh output saved to $OUT_TMP; diff above."
  exit 1
fi
