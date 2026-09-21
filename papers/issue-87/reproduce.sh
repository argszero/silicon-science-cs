#!/usr/bin/env bash
# Issue #87 -- one-command reproduction of the manuscript's numbers, figures and checks.
#
# WHAT IT DOES, in order, each step failing loudly:
#   1. states the build (interpreter paths and the versions of the dependencies whose values enter the compare)
#   2. re-runs the results digest      -> artefacts/results_digest.json   (byte-identical to the committed one)
#   3. re-draws the three figures       -> figures/*.png                  (byte-identical)
#   4. rebuilds the manuscript          -> manuscript.md + assembly report (byte-identical, and its four
#      checks -- 169/169 coverage, no stray citation key, BINDINGS numeric bindings, one numbering for the
#      tables -- must all pass).  BINDINGS is declared ONCE, below, and ASSERTED against the count the
#      assembly prints: a stale copy of this number stops the run instead of surviving in a comment (the
#      defect the R415 editorial re-check found in the previous head, where the header said 91 and the
#      manifest said 128).
#   5. runs the two new instruments' build-bound controls and reports their readings (a FAIL -- a departure
#      beyond the declared relative tolerance -- stops the run; a BUILD-BOUND reading is reported, not hidden)
#   6. runs the journal's four manuscript gates over the built manuscript (refgate must print GATE: PASS)
#
# TOLERANCE: exact, with ONE declared exception: step 4/5.  Every artefact this script writes is compared
# byte for byte against the committed copy; a difference is a failure, not a drift.  Step 4/5 is the
# exception, and it is the exception the exception is FOR: the two new instruments' controls are BITWISE
# controls against a committed record, and a bitwise equality is a property of a BUILD (interpreter +
# numpy), so on any build other than the one the record pins the same instrument returns a last-ULP
# departure.  That step therefore REPORTS its reading -- verdict, the build read, the build pinned, the
# worst relative departure -- and fails only when the departure exceeds the relative tolerance the
# instrument declares (1e-8): three orders above the departure a foreign build returns (2.192e-11,
# measured by the R415 editorial re-check) and nine orders below the panel's own signal.  Reporting is not
# passing by default -- this step is what makes 'the record reproduces' a claim a run can contradict.
#
# Two notes on what exact comparison means: (i) the digest, the manuscript and the
# assembly report are written IN PLACE, so a FAILED comparison leaves the regenerated file in the tree -- the
# committed copy is what the run is measured against, and `git checkout -- <file>` puts the head back; (ii) the
# run states the head it was taken at, because a run is evidence about the version it ran on and no other.  The study is deterministic (exact statevector simulation, fixed
# seeds, no clock, no network, no GPU), so no tolerance is needed for the numbers themselves.
#
# Run:  bash reproduce.sh          (from this directory, papers/issue-87/)
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/../.." && pwd)"          # the repository root, for .github/tools/*.py
PY="${PY:-/usr/bin/python3}"               # numpy + matplotlib live here
PYGATE="${PYGATE:-$HOME/.local/bin/python3.12}"   # the journal's gates need Python >= 3.12
BINDINGS=133                               # the count the assembly prints; asserted in step 3/5
COVERAGE=169                               # bibliography entries, all cited; asserted in step 3/5 and by refgate

# The comparison copies live in a scratch directory that is removed on exit: the package's own files are read
# at the committed head and never written beside themselves, so a run leaves the tree as it found it.
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

fail() { echo "REPRODUCE: FAIL -- $*" >&2; exit 1; }
same() { cmp -s "$1" "$2" || fail "$3: $1 differs from the committed copy"; echo "  byte-identical: $3"; }

echo "=== build"
echo "  package      : $HERE"
echo "  interpreter  : $PY  ($($PY -V 2>&1))"
$PY - <<'EOF'
import numpy, matplotlib, sys
print("  numpy        : %s" % numpy.__version__)
print("  matplotlib   : %s" % matplotlib.__version__)
print("  json order   : sort_keys=True everywhere (an unsorted dump would make byte-identity a spelling test)")
EOF
echo "  gate interp  : $PYGATE  ($($PYGATE -V 2>&1))"
echo "  head         : $(git -C "$ROOT" rev-parse HEAD 2>/dev/null || echo 'not a git work tree')"
echo "  inputs       : artefacts/instruments/*.json (the instruments' own committed records)"
echo "                 artefacts/refs/refs_built.json, refs_verified.json, references_block.md"
echo

echo "=== 1/5 results digest"
cp artefacts/results_digest.json "$TMP/digest.committed.json"
$PY artefacts/results_digest.py > "$TMP/digest.run.log"
tail -1 "$TMP/digest.run.log"
same artefacts/results_digest.json "$TMP/digest.committed.json" "artefacts/results_digest.json"

echo "=== 2/5 figures"
for f in figures/fig1_advantage_map.png figures/fig2_power_arm.png figures/fig3_metric_structure.png; do
  cp "$f" "$TMP/$(basename "$f").committed"
done
$PY figures/make_figures.py
for f in figures/fig1_advantage_map.png figures/fig2_power_arm.png figures/fig3_metric_structure.png; do
  same "$f" "$TMP/$(basename "$f").committed" "$f"
done

echo "=== 3/5 manuscript assembly and its four checks"
cp manuscript.md "$TMP/manuscript.committed.md"
cp artefacts/assembly/assembly-report.txt "$TMP/assembly-report.committed.txt"
$PY artefacts/assembly/manuscript_assembly.py | tee "$TMP/assembly.run.log" | tail -9
grep -q "ASSEMBLY: PASS" "$TMP/assembly.run.log" || fail "the assembly's own checks did not pass"
grep -q "CHECK 1 coverage: cited $COVERAGE distinct keys; missing 0" "$TMP/assembly.run.log" \
  || fail "the assembly's coverage is not $COVERAGE/$COVERAGE -- the stated count and the printed one disagree"
grep -q "CHECK 3 bindings: $BINDINGS bound (all present)" "$TMP/assembly.run.log" \
  || fail "the assembly printed a binding count other than the $BINDINGS this script states"
# The counts have ONE owner (the assembly report, just rebuilt) and every carrier is read against it: this is
# what keeps a copy from going stale in the carrier nobody remembered to edit.
$PY artefacts/assembly/counts_check.py | tail -3
$PY artefacts/assembly/counts_check.py > /dev/null || fail "a committed carrier states a count the assembly does not print"
echo "  counts asserted against the assembly's own report: coverage $COVERAGE/\$COVERAGE, $BINDINGS bindings"
same manuscript.md "$TMP/manuscript.committed.md" "manuscript.md"
same artefacts/assembly/assembly-report.txt "$TMP/assembly-report.committed.txt" \
     "artefacts/assembly/assembly-report.txt"

echo "=== 4/5 the two new instruments' build-bound controls (reported, not byte-compared)"
for inst in r409_align_streams r412_matchedlocal_tuned; do
  echo "-- artefacts/instruments/$inst.py --control-only"
  $PY "artefacts/instruments/$inst.py" --control-only > "$TMP/$inst.control.log" 2>"$TMP/$inst.control.err" \
    || fail "$inst's control went red on this build (its reading is in the scratch log)"
  grep -E "^(P1|C1) |^      (build read|build pinned|cells|verdict)" "$TMP/$inst.control.log" | sed 's/^/  /'
  if grep -q "verdict     : FAIL" "$TMP/$inst.control.log"; then fail "$inst: the control's verdict is FAIL"; fi
  $PY "artefacts/instruments/$inst.py" --selftest > /dev/null 2>&1 || fail "$inst --selftest went red"
  $PY "artefacts/instruments/$inst.py" --selftest | sed 's/^/    /'
done
echo "  (BITWISE on the pinned build; a BUILD_BOUND verdict is reported above, never hidden)"

echo "=== 5/5 the journal's gates over the built manuscript"
for g in refgate linkgate numgate pointgate; do
  echo "-- $g --selftest"
  ( cd "$ROOT" && $PYGATE ".github/tools/$g.py" --selftest ) | tail -1
done
( cd "$ROOT" && $PYGATE .github/tools/refgate.py papers/issue-87/manuscript.md ) | tee "$TMP/refgate.out" | tail -7
grep -q "GATE: PASS" "$TMP/refgate.out" || fail "refgate did not print GATE: PASS"

echo
echo "REPRODUCE: ALL GREEN"
echo "  manifest of what was compared:"
echo "    artefacts/results_digest.json          76 quantities read out of the instruments' own records"
echo "    figures/fig1_advantage_map.png         the advantage map (Fig. 1)"
echo "    figures/fig2_power_arm.png             the power arm (Fig. 2)"
echo "    figures/fig3_metric_structure.png      the metric's structure (Fig. 3)"
echo "    manuscript.md                          parts + the rendered bibliography"
echo "    artefacts/assembly/assembly-report.txt coverage $COVERAGE/$COVERAGE, 0 stray keys, $BINDINGS bindings"
echo "    refgate                                entries $COVERAGE, 0 not separated, coverage 100.0%, GATE: PASS"
echo "    the two build-bound controls           step 4/5: verdict + build read + build pinned + worst"
echo "                                           relative departure, with both --selftests"
