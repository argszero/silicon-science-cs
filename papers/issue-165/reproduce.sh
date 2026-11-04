#!/bin/bash
# issue-165 -- one command to reproduce every published number.
# DECLARED_STEPS: 5
#
# Contract (this journal's convention):
#   exit 0  every declared step ran and agreed
#   exit 3  nothing failed, but some step could not run here (declared NOT RUN, never read as a pass)
#   exit N  N steps failed
#
# Each step re-derives a committed artefact from the committed data and compares BYTES. The step count
# in the header above is read back out of this file and compared with the number of steps that
# actually ran, because a header nobody checks is a comment: a step silently deleted from this script
# would otherwise leave "ALL GREEN (5 steps)" printed by a run of four.
set -u

SELF=$0
case "$SELF" in /*) ;; *) SELF=$PWD/$SELF ;; esac
HERE=$(cd "$(dirname "$SELF")" && pwd)
SELF=$HERE/$(basename "$SELF")
cd "$HERE" || exit 1

PY=${PYTHON:-python3}

# Figures are the one artefact that needs matplotlib. Analysis, the manuscript render and the number
# gate are standard-library only, so the paper's NUMBERS reproduce on any python3; a reader whose
# default interpreter lacks matplotlib would otherwise get a NOT RUN for a step that can perfectly
# well run here. Pick the best available interpreter for that one step, and say which was used.
FIGPY=$PY
if ! "$FIGPY" -c 'import matplotlib' >/dev/null 2>&1; then
  for cand in /usr/bin/python3 python3.13 python3.12 python3.11 /usr/local/bin/python3; do
    if command -v "$cand" >/dev/null 2>&1 && "$cand" -c 'import matplotlib' >/dev/null 2>&1; then
      FIGPY=$cand
      break
    fi
  done
fi

RUN_STEPS=0
FAILED=0
NOTRUN=0

step () {
  name=$1; shift
  RUN_STEPS=$((RUN_STEPS + 1))
  printf '[%d] %-44s ' "$RUN_STEPS" "$name"
  out=$("$@" 2>&1); rc=$?
  if [ "$rc" -eq 0 ]; then
    printf 'ok\n'
  elif [ "$rc" -eq 3 ]; then
    printf 'NOT RUN\n'; NOTRUN=$((NOTRUN + 1))
    printf '%s\n' "$out" | sed 's/^/       /'
  else
    printf 'FAILED (exit %s)\n' "$rc"; FAILED=$((FAILED + 1))
    printf '%s\n' "$out" | sed 's/^/       /'
  fi
}

# 1. The reader must hold the same bytes we measured. Digests are over the DECOMPRESSED arms, because
#    a digest of the .gz would pin our compression choice rather than the data's identity.
digests () {
  "$PY" - <<'EOF'
import json, os, sys
sys.path.insert(0, ".")
import analysis
for arm in ("cs", "social_sciences"):
    analysis.load(arm)
    print("  %-16s digest verified against refs/DIGESTS.json" % arm)
EOF
}

# 2. The numbers: recompute results.json from the committed arms and compare byte for byte.
analysis_check () { "$PY" analysis.py --check; }

# 3. The prose: re-render the manuscript from the template and compare byte for byte.
manuscript_check () { "$PY" make_manuscript.py --check; }

# 4. The figures: redraw into a temp directory and compare byte for byte.
figures_check () { "$FIGPY" make_figures.py --check; }

# 5. Every number printed in the manuscript must be a form the artefact can produce at that precision.
numbers_check () { "$PY" check_numbers.py; }

echo "issue-165 reproduce -- $(pwd)"
echo "  numbers: $PY$( [ "$PY" = "$FIGPY" ] && echo "" || echo "   figures: $FIGPY" )"
echo
step "committed arm digests"            digests
step "results.json recomputed"         analysis_check
step "manuscript.md re-rendered"       manuscript_check
step "figures redrawn"                 figures_check
step "printed numbers all derivable"   numbers_check
echo

DECLARED_STEPS=$(sed -n 's/^# DECLARED_STEPS: *\([0-9][0-9]*\).*/\1/p' "$SELF")
if [ -z "$DECLARED_STEPS" ]; then
  echo "REPRODUCE: HEADER MISSING -- no '# DECLARED_STEPS: n' line in $SELF" >&2
  exit 1
fi
if [ "$DECLARED_STEPS" != "$RUN_STEPS" ]; then
  echo "REPRODUCE: STEP COUNT MISMATCH -- header declares $DECLARED_STEPS, this run took $RUN_STEPS" >&2
  echo "  a step was added or removed without the header following it" >&2
  exit 1
fi

if [ "$FAILED" -gt 0 ]; then
  echo "REPRODUCE: FAILED -- $FAILED of $RUN_STEPS steps disagreed with the committed artefacts" >&2
  exit "$FAILED"
fi
if [ "$NOTRUN" -gt 0 ]; then
  echo "REPRODUCE: $NOTRUN of $RUN_STEPS steps NOT RUN, the rest green -- this is NOT a pass"
  exit 3
fi
echo "REPRODUCE: ALL GREEN ($RUN_STEPS steps)"
exit 0
