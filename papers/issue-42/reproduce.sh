#!/usr/bin/env bash
# One-command reproduction for issue #42.
#
#   bash reproduce.sh
#
# Runs the four instruments in an isolated build directory, compares their output with the
# committed artefacts, verifies every calibration quote against the committed evidence, checks the
# manuscript's GENERATED bibliography against the file that renders its form (`refs_render.py
# --check`, plus `refs_build_display.py --check` for the data the renderer reads), and asserts every
# number quoted in the manuscript against the artefact that produced it.
#
# THE BUILD IS A COORDINATE. Step 0 prints this run's build (interpreter version and numpy version)
# beside the build the artefacts were re-derived under (`build.json`), and checks that the block the
# spec states is the block a fresh render of that record produces. Step 2 compares the artefacts and,
# when they differ, says WHY: on the named build a difference is a failure, while on another build a
# difference that is inside the declared band (or a digest recomputed from the same artefact) is
# reported as a COORDINATE -- this run's build differs, so the comparison is not applicable -- and
# never as a defect of the artefact.
#
# THE EVIDENCE LOGS ARE RE-DERIVED. Step 6 runs each correction checker in `--check` mode: the checker
# re-takes its readings, renders the log it would write, and compares it with the committed copy -- the
# two coordinate lines (which name the build and the tree) declared rather than compared, and a reading
# that cannot be taken here reported as not taken instead of as a disagreement. A checker writes no log
# unless `--log` asks for one, so a reader's run cannot overwrite the evidence they are reading.
#
# Expected final line, on the named build: "REPRODUCE: ALL GREEN" (exit 0).
# On another build with explainable differences:
#     REPRODUCE: COORDINATE MISMATCH - ... (exit 4, and steps 3-5 still ran).
# On a difference the build does not explain: "REPRODUCE: FAILED" (exit 1).
set -euo pipefail
cd "$(dirname "$0")"
ROOT="$PWD"
BUILD="$(mktemp -d)"

# Preflight: the instruments import numpy (derived from the source, not from memory).
# Pick an interpreter that has it; fail with the requirement if none does.
pick_python() {
  for c in "${PYTHON:-}" python3 /usr/bin/python3; do
    [ -n "$c" ] || continue
    if command -v "$c" > /dev/null 2>&1 && "$c" -c "import numpy" > /dev/null 2>&1; then
      echo "$c"; return 0
    fi
  done
  return 1
}
PY="$(pick_python)" || {
  echo "FATAL: no interpreter with numpy found."
  echo "Required: python3 with numpy (the instruments); matplotlib is needed only for figures."
  echo "Hint: python3 -m pip install --user numpy   or set PYTHON=/path/to/python3"
  exit 1
}
echo "interpreter: $PY ($("$PY" -c 'import sys; print(sys.version.split()[0])'))"
trap 'rm -rf "$BUILD"' EXIT

# The revision, DECLARED: this may be a plain directory (an export carries no .git), and a reading
# should say which version of the package it was taken on.
HEAD="$(git rev-parse HEAD 2>/dev/null || echo 'not declared (no .git in this tree)')"

echo
echo "== 0. build coordinate =="
"$PY" build_record.py --line
"$PY" build_record.py --check

echo "== 1. instruments (isolated build dir) =="
cp instruments/instrument_v*.py "$BUILD/"
cp artefacts/calibration_dossier.json "$BUILD/"
cp -R evidence "$BUILD/"
( cd "$BUILD" && for v in 0 1 2 3; do
    printf '   instrument_v%s ... ' "$v"
    "$PY" "instrument_v$v.py" > /dev/null
    echo "ran"
  done )

echo "== 2. compare produced artefacts with committed ones =="
# The comparison is unchanged (canonical digests); what is added is the ATTRIBUTION, so a difference
# on another build is reported as the coordinate it is rather than as a defect of the artefact.
set +e
"$PY" artefact_compare.py --build "$BUILD" --root "$ROOT"
CMP=$?
set -e
if [ "$CMP" = 1 ]; then
  echo
  echo "REPRODUCE: FAILED - the artefacts differ and the build does not explain it (step 2 above)."
  exit 1
fi

echo "== 3. calibration quotes vs committed evidence =="
"$PY" verify_quotes.py

echo "== 4. references (generated form) =="
"$PY" refs_build_display.py --check
"$PY" refs_render.py --check

echo "== 5. manuscript numbers vs artefacts =="
"$PY" assemble.py > /dev/null
"$PY" trace_check.py
"$PY" validate.py | tail -2

echo "== 6. correction checkers (each re-derives its evidence log and compares it) =="
"$PY" verify_correction_r1.py --check --head "$HEAD"
"$PY" verify_correction_r2.py --check --head "$HEAD"

echo
if [ "$CMP" = 4 ]; then
  echo "REPRODUCE: COORDINATE MISMATCH - this run's build is not the named build and every difference"
  echo "           is attributed to it. Nothing above is a defect of the artefact: re-run under the"
  echo "           named build in build.json for the exact verdict (see README.md -> the tolerance rule)."
  exit 4
fi
echo "REPRODUCE: ALL GREEN"
