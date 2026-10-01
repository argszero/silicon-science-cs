#!/usr/bin/env bash
# Reproduce issue #114: the instrument, the artefact, the figures, and the manuscript's
# numbers -- each checked against what is COMMITTED here, not merely re-run.
#
#     bash reproduce.sh          # expected final line: REPRODUCE: ALL GREEN
#
# Requires python3 (standard library only; no pip, no network) and shasum/cmp.
#
# What "reproduce" means in this package, in three separate claims, each with its own step:
#   1. the instrument is deterministic and self-audited   (run_all.sh: batteries + plant
#      audits, and two independent runs of the decisive run required byte-identical)
#   2. the COMMITTED artefact is what the code produces   (canonical.py: regenerate to a
#      temp file and diff against canonical_results.json)
#   3. the COMMITTED figures and the manuscript's numbers are views of that artefact
#      (make_figures.py --check, assemble.py --check, check_manuscript.py, check_aggregates.py)
# Claim 2 is the one a reader of the paper depends on and the one a naive "run it twice"
# tolerance does NOT cover, so it is stated and executed separately.
set -u
cd "$(dirname "$0")"
fail=0

step() {
  local name="$1"; shift
  echo "===== $name"
  if "$@"; then :; else echo "  >>> FAILED: $name"; fail=1; fi
}

step run_all.sh          bash run_all.sh
step canonical           python3 canonical.py
step figures             python3 make_figures.py --check
step assemble            python3 assemble.py --check
step manuscript_numbers  python3 check_manuscript.py
step grid_claims         python3 check_aggregates.py

echo
if [ "$fail" -eq 0 ]; then echo "REPRODUCE: ALL GREEN"; else echo "REPRODUCE: FAILURES PRESENT"; fi
exit "$fail"
