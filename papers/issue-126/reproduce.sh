#!/usr/bin/env bash
# reproduce.sh -- issue #126: re-run every instrument from the committed inputs and check that every
# artefact is BYTE-IDENTICAL to the committed one.
#
# Tolerance: exact.  Every instrument is deterministic (no randomness except a stated seed), so the
# comparison is a hash equality and a deviation is a failure rather than a drift.  The instruments are
# run twice in effect: first their own `--selftest` (the plants that prove each certificate can fire),
# then the measurement itself.
#
#   bash reproduce.sh                 reproduce + verify against the manifest
#   bash reproduce.sh --update-manifest   rewrite the manifest from a green run (authoring only)
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
cd "$HERE" || exit 2
MANIFEST="$HERE/SHA256SUMS.reproduce"
MANUSCRIPT="$HERE/manuscript.md"

UPDATE=0
VERIFY_ONLY=0
[ "${1:-}" = "--update-manifest" ] && UPDATE=1
[ "${1:-}" = "--verify-only" ] && VERIFY_ONLY=1

# --- interpreter: selected by the modules the recompute path actually imports, and it says which ----
PY=""
for c in /usr/bin/python3 python3 python; do
  command -v "$c" >/dev/null 2>&1 || continue
  if "$c" -c "import numpy" >/dev/null 2>&1; then PY="$c"; break; fi
done
if [ -z "$PY" ]; then
  echo "REPRODUCE: NO INTERPRETER WITH numpy FOUND -- the external-validation arm cannot run"
  exit 2
fi
"$PY" - <<'PYEOF' || exit 2
import sys, json
try:
    import numpy
except ImportError:
    sys.exit("numpy missing")
print("interpreter: python %s, numpy %s" % (sys.version.split()[0], numpy.__version__))
PYEOF

hash_of() { "$PY" -c 'import hashlib,sys;print(hashlib.sha256(open(sys.argv[1],"rb").read()).hexdigest())' "$1"; }

FAIL=0
STEPS=0
NOC=0

# --- 1..12: the instruments -------------------------------------------------------------------------
INSTRUMENTS="spike_v0 spike_v1 spike_v2 spike_v3 spike_real spike_real2 spike_real3 spike_learn spike_learn2 spike_mm spike_lib spike_struct"
# the step count the manuscript quotes: the instruments + figures + reference list + the number check +
# the figure check + the citation report.  It is DERIVED from the list, so adding an instrument cannot
# leave the quoted line stale.
ALL_STEPS=$(( $(echo $INSTRUMENTS | wc -w | tr -d ' ') + 5 ))
if [ "$VERIFY_ONLY" = "0" ]; then
for name in $INSTRUMENTS; do
  STEPS=$((STEPS + 1))
  if ! "$PY" "$name.py" --selftest >"/tmp/${name}_selftest.log" 2>&1; then
    echo "FAIL [$name --selftest]"; tail -5 "/tmp/${name}_selftest.log"; FAIL=$((FAIL + 1)); continue
  fi
  if ! "$PY" "$name.py" >"/tmp/${name}_run.log" 2>&1; then
    echo "FAIL [$name run]"; tail -5 "/tmp/${name}_run.log"; FAIL=$((FAIL + 1)); continue
  fi
done

# --- 13: the figures, then the generators -----------------------------------------------------------
STEPS=$((STEPS + 1))
if ! "$PY" make_figures.py >/tmp/make_figures.log 2>&1; then
  echo "FAIL [make_figures]"; tail -5 /tmp/make_figures.log; FAIL=$((FAIL + 1))
fi

STEPS=$((STEPS + 1))
if ! "$PY" build_refs.py >/tmp/build_refs.log 2>&1; then
  echo "FAIL [build_refs]"; tail -5 /tmp/build_refs.log; FAIL=$((FAIL + 1))
fi

STEPS=$((STEPS + 1))
if ! "$PY" check_numbers.py >/tmp/check_numbers.log 2>&1; then
  echo "FAIL [check_numbers]"; tail -5 /tmp/check_numbers.log; FAIL=$((FAIL + 1))
fi

STEPS=$((STEPS + 1))
if ! "$PY" check_figures.py >/tmp/check_figures.log 2>&1; then
  echo "FAIL [check_figures]"; tail -5 /tmp/check_figures.log; FAIL=$((FAIL + 1))
fi

STEPS=$((STEPS + 1))
if ! "$PY" refscan126.py --report >/tmp/refscan_report.log 2>&1; then
  echo "FAIL [refscan --report]"; tail -5 /tmp/refscan_report.log; FAIL=$((FAIL + 1))
fi
fi   # end of the regeneration steps (--verify-only skips them)

# --- the byte-identity check ------------------------------------------------------------------------
ARTEFACTS=""
for name in $INSTRUMENTS; do ARTEFACTS="$ARTEFACTS ${name}_results.json"; done
ARTEFACTS="$ARTEFACTS figures/fig1_floor.png figures/fig2_width_law.png figures/fig3_order_axis.png figures/fig4_lanes.png figures/fig5_library_structure.png manuscript.md references.md reference-check.md"

if [ "$UPDATE" = "1" ]; then
  : >"$MANIFEST"
  for f in $ARTEFACTS; do echo "$(hash_of "$f")  $f" >>"$MANIFEST"; done
  echo "manifest rewritten: $(wc -l <"$MANIFEST" | tr -d ' ') files"
else
  if [ ! -f "$MANIFEST" ]; then echo "REPRODUCE: NO MANIFEST ($MANIFEST)"; exit 2; fi
  while read -r want path; do
    [ -z "${path:-}" ] && continue
    if [ ! -f "$path" ]; then echo "MISSING $path"; FAIL=$((FAIL + 1)); continue; fi
    got="$(hash_of "$path")"
    if [ "$got" != "$want" ]; then
      echo "CHANGED $path"; echo "  committed ${want:0:16}"; echo "  this run  ${got:0:16}"
      FAIL=$((FAIL + 1))
    fi
  done <"$MANIFEST"
fi

# --- the manuscript must quote the line this script prints (the claim has a reader) -----------------
LINE="REPRODUCE: ALL GREEN ($ALL_STEPS steps, 0 failures)"
if [ -f "$MANUSCRIPT" ]; then
  if ! grep -qF "$LINE" "$MANUSCRIPT"; then
    echo "FAIL [manuscript does not quote the reproduce line]"
    echo "  expected to find: $LINE"
    FAIL=$((FAIL + 1))
  fi
fi

if [ "$FAIL" != "0" ]; then
  echo "REPRODUCE: $FAIL FAILURE(S) over $STEPS steps"
  exit 1
fi
echo "$LINE"
