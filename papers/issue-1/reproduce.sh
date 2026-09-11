#!/usr/bin/env bash
# =============================================================================
# One-command reproduction for issue #1
#
#   "When Should an Agent Retrieve Instead of Read?"
#
# WORKING DIRECTORY: this script must be run from anywhere, but it always cd's to
# its own directory, the package root, and every path it prints is relative to that:
#
#     papers/issue-1/
#
# Expected output is stated in README.md. Two tiers:
#
#   heavy tier (needs PyTorch): reader-fidelity gate -> 48-cell sweep -> derivation
#                               -> figures -> validation. Recomputes canonical_results.json.
#   light tier (no PyTorch):    validation of the committed canonical_results.json
#                               -> figures regenerated from it.
#
# The light tier exists because this package's reader and retriever are dependency-free
# ports that still need PyTorch for the tensor kernels, and the machine this was developed
# on cannot install PyTorch from the network (the download stalls). The light tier verifies
# every number in the manuscript against the committed artefact; the heavy tier recomputes
# that artefact from scratch. Say which one you ran when citing the result.
#
# Overrides:  EMRG_PYTHON=/path/to/python   interpreter with PyTorch (heavy tier)
#             EMRG_FIG_PYTHON=/path/to/python  interpreter with matplotlib (figures)
# =============================================================================
set -u

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$HERE" || { echo "cannot enter $HERE"; exit 1; }

echo "reproduce.sh -- issue #1 reproduction"
echo "working directory: $HERE"

TMP="$(mktemp -d "${TMPDIR:-/tmp}/issue1-repro.XXXXXX")" || exit 1
cleanup() { rm -rf "$TMP"; }
trap cleanup EXIT

has_mod() { "$1" -c "import $2" >/dev/null 2>&1; }

pick() {  # pick <module> <candidate...>
    mod="$1"; shift
    for c in "$@"; do
        [ -n "$c" ] || continue
        command -v "$c" >/dev/null 2>&1 || continue
        if has_mod "$c" "$mod"; then echo "$c"; return 0; fi
    done
    return 1
}

PY_TORCH="$(pick torch "${EMRG_PYTHON:-}" python3 /usr/bin/python3 "$HERE/.venv/bin/python" "$HOME/.venv/bin/python" || true)"
PY_FIG="$(pick matplotlib "${EMRG_FIG_PYTHON:-}" /usr/bin/python3 python3 || true)"

echo "interpreter (torch):      ${PY_TORCH:-none found}"
echo "interpreter (matplotlib): ${PY_FIG:-none found}"

[ -n "$PY_FIG" ] || { echo "FATAL: no interpreter with matplotlib; the figures are a completeness requirement."; exit 1; }

T0=$(date +%s)
FAILED=0
declare -a LOG

run_step() {  # run_step <label> <interpreter> <script>
    label="$1"; py="$2"; script="$3"
    t0=$(date +%s)
    if "$py" -u "$script" > "$TMP/$label.out" 2>&1; then st=ok; else st=FAILED; FAILED=1; fi
    t1=$(date +%s)
    printf '%-22s %-7s %4ds\n' "$label" "$st" "$((t1 - t0))"
    LOG+=("step $label: $st (${label}_seconds=$((t1 - t0)))")
    [ "$st" = ok ] || { echo "--- last 40 lines of $label ---"; tail -40 "$TMP/$label.out"; }
}

if [ -n "$PY_TORCH" ]; then
    echo "TIER: heavy (recomputing the canonical artefact from scratch)"
    run_step fidelity_gate  "$PY_TORCH" eval_fidelity.py
    run_step sweep_and_derive "$PY_TORCH" canonical_runner.py
else
    echo "TIER: light (validating the committed canonical artefact)"
    echo "  PyTorch was not found, so the sweep is NOT recomputed. To run the heavy tier:"
    echo "    EMRG_PYTHON=/path/to/python-with-torch bash reproduce.sh"
    LOG+=("note light tier: torch interpreter not found, sweep skipped")
fi

run_step figures  "$PY_FIG" make_figures.py
run_step validate "$PY_FIG" validate.py

if [ "$FAILED" -eq 0 ]; then RESULT=PASS; else RESULT=FAIL; fi

SHA="$(python3 - <<'PY' 2>/dev/null || echo unknown
import json
print(json.load(open("canonical_results.json"))["sha256"][:16])
PY
)"
VC="$(grep -E '^VALIDATE' "$TMP/validate.out" 2>/dev/null | tail -1 || echo 'VALIDATE unknown')"
T1=$(date +%s)

echo
echo "canonical payload sha256: ${SHA}"
echo "${VC}"
echo "RESULT: ${RESULT} | wall-clock $((T1 - T0)) s"

{
    echo "# reproduce.sh run log -- issue #1"
    echo "# working directory: papers/issue-1"
    echo "# tier: $([ -n "$PY_TORCH" ] && echo heavy || echo light)"
    echo "# torch interpreter: ${PY_TORCH:-none}"
    echo "# figures interpreter: ${PY_FIG:-none}"
    for l in "${LOG[@]}"; do echo "$l"; done
    echo "canonical_payload_sha256_prefix: ${SHA}"
    echo "validate: ${VC}"
    echo "result: ${RESULT}"
    echo "total_wall_clock_s: $((T1 - T0))"
    echo "run_at_utc: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
} > run.log

echo "wrote run.log"
exit $([ "$FAILED" -eq 0 ] && echo 0 || echo 1)
