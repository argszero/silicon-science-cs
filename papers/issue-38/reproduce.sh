#!/usr/bin/env bash
# One-command reproduction for issue #38.
#
# It runs the canonical runner (which rewrites canonical_results.json and run.log),
# regenerates the figures (figures/*.png and figures/manifest.json), and validates the
# artefact (validate.py, which asserts 92 conditions attached to the manuscript's
# claims). It then prints the artefact digest that a verifier compares.
#
# Files this run REWRITES, deliberately:
#     canonical_results.json, run.log, figures/*.png, figures/manifest.json
# No check compares any of those to a stored copy, so the command is re-entrant:
# a second invocation over the same checkout prints the same verdict. The figure
# digests are compared against figures/manifest.json, which is regenerated in the
# same run, so figure bytes may differ across matplotlib builds without failing.
set -euo pipefail
cd "$(dirname "$0")"

# The pipeline needs numpy and matplotlib. The interpreter first on PATH is not
# necessarily the one that has them, so probe for an interpreter that can actually run
# the pipeline rather than assuming: an environment mismatch must be reported, not
# silently substituted. $PY overrides the probe.
pick_python() {
  for cand in ${PY:-} python3 /usr/bin/python3 /usr/local/bin/python3 python; do
    [ -n "$cand" ] || continue
    if command -v "$cand" >/dev/null 2>&1 && "$cand" -c 'import numpy, matplotlib' >/dev/null 2>&1; then
      echo "$cand"; return 0
    fi
  done
  return 1
}
if ! PY="$(pick_python)"; then
  echo "RESULT: FAIL - no interpreter on this machine has both numpy and matplotlib."
  echo "  install them (e.g. pip install numpy matplotlib) or set PY=<interpreter>."
  exit 1
fi
echo "== issue #38 reproduction (interpreter: $($PY -c 'import sys; print(sys.executable)'), $($PY -c 'import matplotlib; print("matplotlib " + matplotlib.__version__)'))"
echo "== rewrites: canonical_results.json, run.log, figures/*.png, figures/manifest.json"

start=$(date +%s)
echo "-- canonical runner"
$PY canonical_runner.py
echo "-- figures"
$PY make_figures.py
echo "-- validation"
$PY validate.py

digest=$($PY - <<'PY'
import hashlib
print(hashlib.sha256(open("canonical_results.json", "rb").read()).hexdigest())
PY
)
end=$(date +%s)
echo
echo "artefact sha256: $digest"
echo "wall-clock: $((end - start)) s (machine-dependent, not part of any claim)"
echo "RESULT: PASS"
