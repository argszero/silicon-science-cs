#!/bin/bash
# issue-165 -- one command to reproduce every published number.
#
# Contract (this journal's convention):
#   exit 0  every declared step ran and agreed
#   exit 3  nothing failed, but some step could not run here (declared NOT RUN, never read as a pass)
#   exit N  N steps failed
#
# Each step re-derives a committed artefact from the committed data and compares BYTES.
#
# THE STEP COUNT IS COMPUTED, NOT TYPED. `STEP_NAMES` below is the single place the declared steps are
# listed; `DECLARED_STEPS` is the number of names in it, and the run refuses to print a verdict unless
# the steps it actually took equal that number in BOTH directions -- a step deleted from the body while
# its name stays listed, and a step added to the body without being named, are the same failure and both
# exit non-zero. A hand-typed count in a comment is a comment nothing reads: this journal's stepgate
# reads the computed form, so the claim a reader compares against is the one the script derives.
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

# The declared steps, in order. Adding a step means adding its name here as well as its call below;
# leaving the two out of step is caught at the end of the run, not left to a reader to notice.
STEP_NAMES="digests analysis_check manuscript_check figures_check numbers_check refs_check"
DECLARED_STEPS=$(( $(echo $STEP_NAMES | wc -w | tr -d ' ') + 0 ))

RUN_STEPS=0
FAILED=0
NOTRUN=0

step () {
  name=$1; shift
  RUN_STEPS=$((RUN_STEPS + 1))
  if [ "$RUN_STEPS" -gt "$DECLARED_STEPS" ]; then
    printf '[%d] %-44s FAILED (a step with no name in STEP_NAMES)\n' "$RUN_STEPS" "$name"
    FAILED=$((FAILED + 1))
    return 0
  fi
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

# 6. The citation report must still describe the corpus. A report that has drifted from
#    refs/records.json is a claim about references that no longer exists, which is the defect the
#    report exists to prevent.
refs_check () { "$PY" ref_check.py --check; }

echo "issue-165 reproduce -- $(pwd)"
echo "  numbers: $PY$( [ "$PY" = "$FIGPY" ] && echo "" || echo "   figures: $FIGPY" )"
echo
step "committed arm digests"            digests
step "results.json recomputed"         analysis_check
step "manuscript.md re-rendered"       manuscript_check
step "figures redrawn"                 figures_check
step "printed numbers all derivable"   numbers_check
step "reference report matches corpus" refs_check
echo

if [ "$DECLARED_STEPS" != "$RUN_STEPS" ]; then
  echo "REPRODUCE: STEP COUNT MISMATCH -- STEP_NAMES declares $DECLARED_STEPS, this run took $RUN_STEPS" >&2
  echo "  a step was added or removed without STEP_NAMES following it" >&2
  exit 1
fi

if [ "$FAILED" -gt 0 ]; then
  echo "REPRODUCE: FAILED -- $FAILED of $DECLARED_STEPS steps disagreed with the committed artefacts" >&2
  exit "$FAILED"
fi
if [ "$NOTRUN" -gt 0 ]; then
  echo "REPRODUCE: $NOTRUN of $DECLARED_STEPS steps NOT RUN, the rest green -- this is NOT a pass"
  exit 3
fi
echo "REPRODUCE: ALL GREEN ($DECLARED_STEPS steps)"
exit 0
