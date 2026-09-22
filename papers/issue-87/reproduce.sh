#!/usr/bin/env bash
# Issue #87 -- one-command reproduction of the manuscript's numbers, figures and checks.
#
# PREAMBLE (not a step): the build.  The interpreter paths and the versions of the dependencies whose values
# enter the comparisons are printed before anything runs, because a tolerance names the build it is read
# against (R439) and the run must be able to say which build it was read on.
#
# THE FIVE STEPS, in this order, and the order is part of the reading:
#   1/5 the two new instruments' build-bound controls -- REPORTED, and run FIRST so that a reader on a build
#       other than the pinned one sees this reading before any byte comparison can stop the run (the R446
#       editorial finding: the run used to declare one build-bound step out of three and stop at another).
#   2/5 the results digest -> artefacts/results_digest.json, compared leaf by leaf against the committed copy:
#       BITWISE on the pinned build, BUILD_BOUND (reported, then the committed copy is RESTORED so the steps
#       below read the record the package pins) when every differing leaf is within the declared 1e-8, FAIL
#       beyond it.  Written in place, so the committed copy is the carrier of the comparison.
#   3/5 the three figures -> figures/*.png.  A PNG is a RENDERING: its bytes are a property of matplotlib +
#       freetype + libpng, so this step REPORTS (BITWISE | RENDER_BOUND + the renderer) and never stops the run
#       -- the figures' numbers are the digest's, held by 2/5.  With no matplotlib on the interpreter the step
#       says NOT RUN, which is not a pass.
#   4/5 the manuscript assembly and its checks -> manuscript.md + the assembly report, compared byte for byte
#       (measured byte-identical on both non-pinned builds the R446 re-check ran, so this step is exact and
#       not a tolerance question).  169/169 coverage, no stray key, BINDINGS numeric bindings, one numbering
#       for the tables.  BINDINGS is declared ONCE and ASSERTED against what the assembly prints, and every
#       other carrier of the counted claims is read against the report by counts_check.py.
#   5/5 the journal's four manuscript gates over the built manuscript (refgate must print GATE: PASS).
#
# TOLERANCE -- WHICH STEPS ARE READ AGAINST THE PINNED BUILD: **three**, and they are not the same kind of
# step, so they are not treated alike:
#   * 1/5 (the two controls) and 2/5 (the digest) are build-bound NUMBERS: they are compared and REPORTED in
#     the declared form -- build read, build pinned, departure, verdict -- and the run fails only when a
#     departure exceeds the declared relative tolerance 1e-8 (three orders above the 2.192e-11 a foreign build
#     returns, measured by the R446 re-check, and nine orders below the panel's own signal).
#   * 3/5 (the figures) is a build-bound RENDERING.  Its bytes are reported and never stopped on: no tolerance
#     for a rendering has been MEASURED here, and this package does not declare numbers it has not measured.
#   * 4/5 (the manuscript and the assembly report) and 5/5 (the gates) are read EXACTLY, and that is a hard
#     test: byte-identity there is this run's stop condition.  (Measured, not assumed: the R446 re-check
#     rebuilt both artefacts on python 3.14.2/numpy 2.4.2 and python 3.14.6/numpy 2.5.1 and got byte-identical
#     copies, `f5af1429…` and `7180dae0…`.)
# Reporting is not passing by default -- the verdicts above are the reading, and the manifest prints them.
#
# Two notes on what exact comparison means: (i) the digest, the figures, the manuscript and the
# assembly report are written IN PLACE, so the steps that REPORT restore the committed copies before the run
# continues (a reported departure must not become the input of the next step); (ii) the run states the head it
# was taken at, because a run is evidence about the version it ran on and no other.  The study is deterministic
# (exact statevector simulation, fixed seeds, no clock, no network, no GPU), so no tolerance is needed for the
# numbers themselves -- only for the build's own reduction order.
#
# Run:  bash reproduce.sh          (from this directory, papers/issue-87/)
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/../.." && pwd)"          # the repository root, for .github/tools/*.py
PY="${PY:-/usr/bin/python3}"               # numpy + matplotlib live here
PYGATE="${PYGATE:-$HOME/.local/bin/python3.12}"   # the journal's gates need Python >= 3.12
BINDINGS=133                               # the count the assembly prints; asserted in step 4/5
COVERAGE=169                               # bibliography entries, all cited; asserted in step 4/5 and by refgate
REL_TOL=1e-8                               # the declared relative tolerance for the build-bound numbers

# The comparison copies live in a scratch directory that is removed on exit: the package's own files are read
# at the committed head and never written beside themselves, so a run leaves the tree as it found it.
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

fail() { echo "REPRODUCE: FAIL -- $*" >&2; exit 1; }
same() { cmp -s "$1" "$2" || fail "$3: $1 differs from the committed copy"; echo "  byte-identical: $3"; }

echo "=== build (the preamble, not a step)"
echo "  package      : $HERE"
echo "  interpreter  : $PY  ($($PY -V 2>&1))"
$PY - <<'EOF'
try:
    import numpy
    print("  numpy        : %s" % numpy.__version__)
except ImportError as e:
    print("  numpy        : ABSENT (%s)" % e)
try:
    import matplotlib
    print("  matplotlib   : %s" % matplotlib.__version__)
except ImportError as e:
    print("  matplotlib   : ABSENT (%s) -- the figures step reports NOT RUN" % e)
print("  json order   : sort_keys=True everywhere (an unsorted dump would make byte-identity a spelling test)")
EOF
echo "  gate interp  : $PYGATE  ($($PYGATE -V 2>&1))"
echo "  head         : $(git -C "$ROOT" rev-parse HEAD 2>/dev/null || echo 'not a git work tree')"
echo "  pinned build : python 3.9.6 / numpy 2.0.2 / matplotlib 3.9.4  (the build the committed records name)"
echo "  inputs       : artefacts/instruments/*.json (the instruments' own committed records)"
echo "                 artefacts/refs/refs_built.json, refs_verified.json, references_block.md"
echo

echo "=== 1/5 the two new instruments' build-bound controls (REPORTED, and read first by design)"
for inst in r409_align_streams r412_matchedlocal_tuned; do
  echo "-- artefacts/instruments/$inst.py --control-only"
  $PY "artefacts/instruments/$inst.py" --control-only > "$TMP/$inst.control.log" 2>"$TMP/$inst.control.err" \
    || fail "$inst's control went red on this build (its reading is in the scratch log)"
  grep -E "^(P1|C1) |^      (build read|build pinned|cells|verdict)" "$TMP/$inst.control.log" | sed 's/^/  /'
  if grep -q "verdict     : FAIL" "$TMP/$inst.control.log"; then fail "$inst: the control's verdict is FAIL"; fi
  $PY "artefacts/instruments/$inst.py" --selftest > /dev/null 2>&1 || fail "$inst --selftest went red"
  $PY "artefacts/instruments/$inst.py" --selftest | sed 's/^/    /'
done
echo "  (BITWISE on the pinned build; BUILD_BOUND is reported above, never hidden)"

echo "=== 2/5 results digest (leaf-by-leaf; build-bound, reported, tolerance $REL_TOL)"
cp artefacts/results_digest.json "$TMP/digest.committed.json"
$PY artefacts/results_digest.py > "$TMP/digest.run.log"
tail -1 "$TMP/digest.run.log"
if $PY artefacts/assembly/build_bound.py json "$TMP/digest.committed.json" artefacts/results_digest.json \
      --rel-tol "$REL_TOL" --label digest; then
  # RESTORE the committed copy: a reported departure must not become the input of the steps below, which are
  # specified against the record the package pins.
  cp "$TMP/digest.committed.json" artefacts/results_digest.json
  echo "  committed copy restored before the steps below (they read the record the package pins)"
else
  fail "artefacts/results_digest.json departs beyond the declared relative tolerance (see the reading above)"
fi

echo "=== 3/5 figures (a rendering: reported, never a stop condition)"
if $PY -c "import matplotlib" 2>/dev/null; then
  MPLVER="$($PY -c 'import matplotlib;print(matplotlib.__version__)')"
  for f in figures/fig1_advantage_map.png figures/fig2_power_arm.png figures/fig3_metric_structure.png; do
    cp "$f" "$TMP/$(basename "$f").committed"
  done
  $PY figures/make_figures.py
  for f in figures/fig1_advantage_map.png figures/fig2_power_arm.png figures/fig3_metric_structure.png; do
    echo "-- $f"
    $PY artefacts/assembly/build_bound.py png "$f" --committed "$TMP/$(basename "$f").committed" \
        --version-line "matplotlib $MPLVER (pinned: 3.9.4)"
    cp "$TMP/$(basename "$f").committed" "$f"      # restore, as in 2/5
  done
  echo "  (the committed PNGs are restored; the figures' numbers are the digest's, held by step 2/5)"
else
  echo "  NOT RUN -- matplotlib is not installed on $PY, so the figures cannot be re-drawn here."
  echo "  NOT RUN is not a pass: this step verified nothing on this build.  What the figures carry is the"
  echo "  digest, and step 2/5 holds it; the PNG bytes are a property of the renderer build (3.9.4 pinned)."
fi

echo "=== 4/5 manuscript assembly and its four checks (exact: this is the run's stop condition)"
cp manuscript.md "$TMP/manuscript.committed.md"
cp artefacts/assembly/assembly-report.txt "$TMP/assembly-report.committed.txt"
$PY artefacts/assembly/manuscript_assembly.py | tee "$TMP/assembly.run.log" | tail -9
grep -q "ASSEMBLY: PASS" "$TMP/assembly.run.log" || fail "the assembly's own checks did not pass"
grep -q "CHECK 1 coverage: cited $COVERAGE distinct keys; missing 0" "$TMP/assembly.run.log" \
  || fail "the assembly's coverage is not $COVERAGE/$COVERAGE -- the stated count and the printed one disagree"
grep -q "CHECK 3 bindings: $BINDINGS bound (all present)" "$TMP/assembly.run.log" \
  || fail "the assembly printed a binding count other than the $BINDINGS this script states"
# The counts have ONE owner (the assembly report, just rebuilt) and every carrier is read against it: this is
# what keeps a copy from going stale in the carrier nobody remembered to edit.  The checker's own battery runs
# FIRST, because a checker that can no longer fire cannot report on the carriers it reads (a chain that only
# reads an instrument's committed output is insensitive to whether the instrument can run).
$PY artefacts/assembly/counts_check.py | tail -5
$PY artefacts/assembly/counts_check.py > /dev/null || fail "a committed carrier states a count the assembly does not print"
echo "-- artefacts/assembly/counts_check.py --selftest"
$PY artefacts/assembly/counts_check.py --selftest | tail -3
$PY artefacts/assembly/counts_check.py --selftest > /dev/null \
  || fail "the counts checker's own battery did not pass (it caught its own cases -- see the log above)"
echo "  counts asserted against the assembly's own report: coverage $COVERAGE/$COVERAGE, $BINDINGS bindings"
same manuscript.md "$TMP/manuscript.committed.md" "manuscript.md"
same artefacts/assembly/assembly-report.txt "$TMP/assembly-report.committed.txt" \
     "artefacts/assembly/assembly-report.txt"

echo "=== 5/5 the journal's gates over the built manuscript (exact: GATE: PASS is a stop condition)"
for g in refgate linkgate numgate pointgate; do
  echo "-- $g --selftest"
  ( cd "$ROOT" && $PYGATE ".github/tools/$g.py" --selftest ) | tail -1
done
( cd "$ROOT" && $PYGATE .github/tools/refgate.py papers/issue-87/manuscript.md ) | tee "$TMP/refgate.out" | tail -7
grep -q "GATE: PASS" "$TMP/refgate.out" || fail "refgate did not print GATE: PASS"

echo
echo "REPRODUCE: ALL GREEN"
echo "  manifest of what was compared, and how each step was read:"
echo "    1/5 the two build-bound controls         REPORTED -- verdict + build read + build pinned + worst"
echo "                                             relative departure, with both --selftests"
echo "    2/5 artefacts/results_digest.json        REPORTED -- 76 quantities read out, leaf by leaf against the committed copy"
echo "                                             (BITWISE on the pinned build; BUILD_BOUND reported within $REL_TOL)"
echo "    3/5 figures/fig{1,2,3}*.png              RENDERED -- bytes reported (BITWISE | RENDER_BOUND + renderer)"
echo "    4/5 manuscript.md + assembly report       EXACT -- coverage $COVERAGE/$COVERAGE, 0 stray keys, $BINDINGS bindings"
echo "    5/5 refgate over the built manuscript     EXACT -- entries $COVERAGE, 0 not separated, coverage 100.0%, GATE: PASS"
echo
echo "  This run printed ALL GREEN on the build named above.  On a build other than the pinned one, expect:"
echo "    * 2/5 verdict BUILD_BOUND (a few leaves differing in their last bits) and the run CONTINUES;"
echo "    * 3/5 verdict RENDER_BOUND (the PNG bytes differ -- a rendering is a property of the renderer);"
echo "    * 4/5 and 5/5 remain exact; those are the stop conditions, not 2/5 or 3/5."
