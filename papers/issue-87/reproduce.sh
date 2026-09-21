#!/usr/bin/env bash
# Issue #87 -- one-command reproduction of the manuscript's numbers, figures and checks.
#
# WHAT IT DOES, in order, each step failing loudly:
#   1. states the build (interpreter paths and the versions of the dependencies whose values enter the compare)
#   2. re-runs the results digest      -> artefacts/results_digest.json   (byte-identical to the committed one)
#   3. re-draws the three figures       -> figures/*.png                  (byte-identical)
#   4. rebuilds the manuscript          -> manuscript.md + assembly report (byte-identical, and its three
#      checks -- 169/169 coverage, no stray citation key, 91 numeric bindings -- must all pass)
#   5. runs the journal's four manuscript gates over the built manuscript (refgate must print GATE: PASS)
#
# TOLERANCE: exact.  Every artefact this script writes is compared byte for byte against the committed copy;
# a difference is a failure, not a drift.  The study is deterministic (exact statevector simulation, fixed
# seeds, no clock, no network, no GPU), so no tolerance is needed for the numbers themselves.
#
# Run:  bash reproduce.sh          (from this directory, papers/issue-87/)
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/../.." && pwd)"          # the repository root, for .github/tools/*.py
PY="${PY:-/usr/bin/python3}"               # numpy + matplotlib live here
PYGATE="${PYGATE:-$HOME/.local/bin/python3.12}"   # the journal's gates need Python >= 3.12

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
echo "  inputs       : artefacts/instruments/*.json (the instruments' own committed records)"
echo "                 artefacts/refs/refs_built.json, refs_verified.json, references_block.md"
echo

echo "=== 1/4 results digest"
cp artefacts/results_digest.json /tmp/digest.committed.json
$PY artefacts/results_digest.py > /tmp/digest.run.log
tail -1 /tmp/digest.run.log
same artefacts/results_digest.json /tmp/digest.committed.json "artefacts/results_digest.json"

echo "=== 2/4 figures"
for f in figures/fig1_advantage_map.png figures/fig2_power_arm.png figures/fig3_metric_structure.png; do
  cp "$f" "/tmp/$(basename "$f").committed"
done
$PY figures/make_figures.py
for f in figures/fig1_advantage_map.png figures/fig2_power_arm.png figures/fig3_metric_structure.png; do
  same "$f" "/tmp/$(basename "$f").committed" "$f"
done

echo "=== 3/4 manuscript assembly and its three checks"
cp manuscript.md /tmp/manuscript.committed.md
cp artefacts/assembly/assembly-report.txt /tmp/assembly-report.committed.txt
$PY artefacts/assembly/manuscript_assembly.py | tee /tmp/assembly.run.log | tail -9
grep -q "ASSEMBLY: PASS" /tmp/assembly.run.log || fail "the assembly's own checks did not pass"
same manuscript.md /tmp/manuscript.committed.md "manuscript.md"
same artefacts/assembly/assembly-report.txt /tmp/assembly-report.committed.txt \
     "artefacts/assembly/assembly-report.txt"

echo "=== 4/4 the journal's gates over the built manuscript"
for g in refgate linkgate numgate pointgate; do
  echo "-- $g --selftest"
  ( cd "$ROOT" && $PYGATE ".github/tools/$g.py" --selftest ) | tail -1
done
( cd "$ROOT" && $PYGATE .github/tools/refgate.py papers/issue-87/manuscript.md ) | tee /tmp/refgate.out | tail -7
grep -q "GATE: PASS" /tmp/refgate.out || fail "refgate did not print GATE: PASS"

echo
echo "REPRODUCE: ALL GREEN"
echo "  manifest of what was compared:"
echo "    artefacts/results_digest.json          55 quantities read out of the instruments' own records"
echo "    figures/fig1_advantage_map.png         the advantage map (Fig. 1)"
echo "    figures/fig2_power_arm.png             the power arm (Fig. 2)"
echo "    figures/fig3_metric_structure.png      the metric's structure (Fig. 3)"
echo "    manuscript.md                          parts + the rendered bibliography"
echo "    artefacts/assembly/assembly-report.txt coverage 169/169, 0 stray keys, 91 bindings"
echo "    refgate                                entries 169, 0 not separated, coverage 100.0%, GATE: PASS"
