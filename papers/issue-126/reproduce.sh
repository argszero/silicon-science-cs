#!/usr/bin/env bash
# reproduce.sh -- issue #126: re-run every instrument from the committed inputs and check that every
# artefact is BYTE-IDENTICAL to the committed one.
#
# Tolerance: exact.  Every instrument is deterministic (no randomness except a stated seed), so the
# comparison is a hash equality and a deviation is a failure rather than a drift.  Each script is run
# twice in effect: first its own `--selftest` (the plants that prove each certificate can fire), then
# the work itself.
#
#   bash reproduce.sh                    reproduce + verify against the manifest
#   bash reproduce.sh --verify-only      verify the manifest without regenerating anything
#   bash reproduce.sh --update-manifest  rewrite the manifest from a green run (authoring only)
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
cd "$HERE" || exit 2
MANIFEST="$HERE/SHA256SUMS.reproduce"
MANUSCRIPT="$HERE/manuscript.md"
README="$HERE/README.md"

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
import sys
try:
    import numpy
except ImportError:
    sys.exit("numpy missing")
print("interpreter: python %s, numpy %s" % (sys.version.split()[0], numpy.__version__))
PYEOF

hash_of() { "$PY" -c 'import hashlib,sys;print(hashlib.sha256(open(sys.argv[1],"rb").read()).hexdigest())' "$1"; }

FAIL=0
STEPS=0

# --- the instruments, and the two files that must be regenerated BEFORE them (the reference pipeline
#     is upstream of the manuscript, and the manuscript is what the number/figure checks read) --------
INSTRUMENTS="spike_v0 spike_v1 spike_v2 spike_v3 spike_real spike_real2 spike_real3 spike_learn spike_learn2 spike_mm spike_lib spike_struct"
# every script that carries plants, including the checkers: a certificate that cannot fail is decoration
SELFTESTS="$INSTRUMENTS build_refs refs_build_display check_numbers check_figures check_references refscan126"

if [ "$VERIFY_ONLY" = "0" ]; then
  for name in $SELFTESTS; do
    if ! "$PY" "$name.py" --selftest >"/tmp/${name}_selftest.log" 2>&1; then
      echo "FAIL [$name --selftest]"; tail -5 "/tmp/${name}_selftest.log"; FAIL=$((FAIL + 1))
    fi
  done
  for name in $INSTRUMENTS; do
    STEPS=$((STEPS + 1))
    if ! "$PY" "$name.py" >"/tmp/${name}_run.log" 2>&1; then
      echo "FAIL [$name run]"; tail -5 "/tmp/${name}_run.log"; FAIL=$((FAIL + 1))
    fi
  done
  # the figure: drawn from the result artefacts
  STEPS=$((STEPS + 1))
  if ! "$PY" make_figures.py >/tmp/make_figures.log 2>&1; then
    echo "FAIL [make_figures]"; tail -5 /tmp/make_figures.log; FAIL=$((FAIL + 1))
  fi
  # the reference pipeline, in order: body + record layer -> display layer -> the rendered section
  STEPS=$((STEPS + 1))
  if ! "$PY" build_refs.py >/tmp/build_refs.log 2>&1; then
    echo "FAIL [build_refs]"; tail -5 /tmp/build_refs.log; FAIL=$((FAIL + 1))
  fi
  STEPS=$((STEPS + 1))
  if ! "$PY" refs_build_display.py >/tmp/refs_build_display.log 2>&1; then
    echo "FAIL [refs_build_display]"; tail -5 /tmp/refs_build_display.log; FAIL=$((FAIL + 1))
  fi
  STEPS=$((STEPS + 1))
  if ! "$PY" refs_render.py >/tmp/refs_render.log 2>&1; then
    echo "FAIL [refs_render]"; tail -5 /tmp/refs_render.log; FAIL=$((FAIL + 1))
  fi
  # the three product-side readers: numbers, figures, references
  for chk in check_numbers check_figures check_references; do
    STEPS=$((STEPS + 1))
    if ! "$PY" "$chk.py" >"/tmp/${chk}.log" 2>&1; then
      echo "FAIL [$chk]"; tail -5 "/tmp/${chk}.log"; FAIL=$((FAIL + 1))
    fi
  done
  STEPS=$((STEPS + 1))
  if ! "$PY" refscan126.py --report >/tmp/refscan_report.log 2>&1; then
    echo "FAIL [refscan126 --report]"; tail -5 /tmp/refscan_report.log; FAIL=$((FAIL + 1))
  fi
  STEPS=$((STEPS + 1))
  if ! "$PY" refs_render.py --check >/tmp/refs_render_check.log 2>&1; then
    echo "FAIL [refs_render --check]"; tail -5 /tmp/refs_render_check.log; FAIL=$((FAIL + 1))
  fi
fi

# --- the byte-identity check ------------------------------------------------------------------------
ARTEFACTS=""
for name in $INSTRUMENTS; do ARTEFACTS="$ARTEFACTS ${name}_results.json"; done
ARTEFACTS="$ARTEFACTS figures/fig1_floor.png figures/fig2_width_law.png figures/fig3_order_axis.png figures/fig4_lanes.png figures/fig5_library_structure.png manuscript.md references.json refs_display.json refs_authors.json reference-check.md"

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

# --- the manuscript AND the README must quote the line this script prints (a quoted output line is a
# --- claim about a program, so both carriers of the claim are read against the program) --------------
ALL_STEPS=$(( $(echo $INSTRUMENTS | wc -w | tr -d ' ') + 9 ))
LINE="REPRODUCE: ALL GREEN ($ALL_STEPS steps, 0 failures)"
if [ -f "$MANUSCRIPT" ]; then
  if ! grep -qF "$LINE" "$MANUSCRIPT"; then
    echo "FAIL [manuscript does not quote the reproduce line]"
    echo "  expected to find: $LINE"
    FAIL=$((FAIL + 1))
  fi
fi

# the README's counted claims: the same line, and the manifest's size -- each number the README states
# is compared with the number this run measured, so a stale README is a FAILURE and not a typo (R552)
N_ARTEFACTS=$(echo $ARTEFACTS | wc -w | tr -d ' ')
if [ -f "$README" ]; then
  if ! grep -qF "$LINE" "$README"; then
    echo "FAIL [README does not quote the reproduce line]"
    echo "  expected to find: $LINE"
    FAIL=$((FAIL + 1))
  fi
  if ! grep -qF "$N_ARTEFACTS artefacts" "$README"; then
    echo "FAIL [README does not state the manifest's size]"
    echo "  expected to find: $N_ARTEFACTS artefacts"
    FAIL=$((FAIL + 1))
  fi
else
  echo "FAIL [README.md is missing]"; FAIL=$((FAIL + 1))
fi

if [ "$FAIL" != "0" ]; then
  echo "REPRODUCE: $FAIL FAILURE(S) over $STEPS steps"
  exit 1
fi
echo "$LINE"
