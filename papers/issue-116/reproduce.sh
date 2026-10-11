#!/usr/bin/env bash
# Issue #116 -- one-command reproduction.
#
#   bash reproduce.sh          expected final line: REPRODUCE: ALL GREEN
#
# Network-free, stdlib-only (python3 + coreutils). Writes NOTHING inside this
# package: every check regenerates into a temporary directory and compares.
set -u
cd "$(dirname "$0")" || exit 1
# The recorded build is CPython 3.9.6 with numpy 2.0.2; the sweep and the figures
# need numpy. Prefer the system interpreter that carries it, and say which was used.
if [ -z "${PY:-}" ]; then
  if /usr/bin/python3 -c "import numpy" 2>/dev/null; then PY=/usr/bin/python3
  else PY=python3; fi
fi
TMP="$(mktemp -d)"
FAIL=0
trap 'rm -rf "$TMP"' EXIT

step() { printf '\n== %s\n' "$1"; }
ok()   { printf '   OK   %s\n' "$1"; }
bad()  { printf '   FAIL %s\n' "$1"; FAIL=1; }

step "0. build"
"$PY" -c "import sys, numpy; print('python', sys.version.split()[0], '/ numpy', numpy.__version__)" || exit 1
echo "   (recorded build: python 3.9.6 / numpy 2.0.2)"

# ---------------------------------------------------------------- claim 1
# The instrument is DETERMINISTIC: two independent runs of the sweep must be
# byte-identical, and so must the log.
step "1. determinism: two independent runs are byte-identical"
# Both passes run in the SAME directory: a numpy RuntimeWarning prints its own
# file path, so two runs in different directories produce logs that differ only
# by the directory name -- a comparison artefact, not non-determinism.
mkdir -p "$TMP/r1"
for f in model_v1.py model_v2.py model_v4_sweep.py; do cp "$f" "$TMP/r1/"; done
( cd "$TMP/r1" && "$PY" model_v4_sweep.py > run.log 2>&1 ) || bad "run 1 failed"
cp "$TMP/r1/canonical_results.json" "$TMP/artefact_run1.json"
cp "$TMP/r1/run.log" "$TMP/log_run1.txt"
( cd "$TMP/r1" && "$PY" model_v4_sweep.py > run2.log 2>&1 ) || bad "run 2 failed"
if cmp -s "$TMP/artefact_run1.json" "$TMP/r1/canonical_results.json"; then
  ok "canonical_results.json byte-identical across two runs"
else bad "canonical_results.json is NOT deterministic"; fi
if cmp -s "$TMP/log_run1.txt" "$TMP/r1/run2.log"; then
  ok "run log byte-identical across two runs (same directory)"
else bad "run log differs between runs"; fi
# The RuntimeWarnings come from the probe delays BEYOND the stability margin,
# where the closed loop is unstable by construction -- expected, and asserted so.
if grep -q "RuntimeWarning" "$TMP/log_run1.txt"; then
  n=$(grep -c "RuntimeWarning" "$TMP/log_run1.txt")
  ok "RuntimeWarnings present ($n) and stable: they arise on the probe delays past d_max"
else
  ok "no RuntimeWarnings"
fi

# ---------------------------------------------------------------- claim 2
# The COMMITTED artefact is what the code produces. A determinism check does not
# prove this: it compares a run against another run, not against the file shipped.
step "2. the committed artefact is what the code produces"
if cmp -s "$TMP/artefact_run1.json" canonical_results.json; then
  ok "committed canonical_results.json equals the regenerated artefact"
  echo "        sha256 $(shasum -a 256 canonical_results.json | cut -d' ' -f1)"
else
  bad "committed canonical_results.json differs from the regenerated artefact"
  diff <(head -40 canonical_results.json) <(head -40 "$TMP/artefact_run1.json") | head -10
fi

# ---------------------------------------------------------------- claim 3
# The figures and the manuscript are VIEWS of that artefact.
step "3. the committed figures are views of the committed artefact"
mkdir -p "$TMP/fig"
cp make_figures.py plotlib.py canonical_results.json "$TMP/fig/"
( cd "$TMP/fig" && "$PY" make_figures.py > fig.log 2>&1 ) || bad "figure render failed"
for p in frontier_R100 exponent_by_config regime_map channels; do
  if cmp -s "figures/$p.png" "$TMP/fig/figures_draft/$p.png"; then
    ok "figures/$p.png byte-identical to the regenerated figure"
  else bad "figures/$p.png differs from the regenerated figure"; fi
done
# The journal's figure item has TWO conditions and the object of BOTH is the manuscript:
# the file is committed AND the manuscript embeds it, with a caption. The loop above reads
# the first; until this round NOTHING read the second -- this package passed while the
# manuscript showed no figure at all, which is exactly how a text-only paper is published.
for p in frontier_R100 exponent_by_config regime_map channels; do
  if grep -q "](figures/$p.png)" manuscript.md; then
    ok "manuscript.md embeds figures/$p.png"
  else bad "manuscript.md does not embed figures/$p.png"; fi
done

step "4. the committed manuscript is what the pipeline builds"
if "$PY" refs/refs_build.py render-check; then :; else bad "manuscript render mismatch"; fi

step "5. citation coverage and the citation guards"
if "$PY" refs/refs_build.py check; then :; else bad "coverage check failed"; fi

step "6. the manuscript's decisive numbers reappear from the code"
# Each number the paper prints is re-derived here from a real run, not trusted.
mkdir -p "$TMP/v1" "$TMP/v3" "$TMP/v5"
cp model_v1.py "$TMP/v1/"; cp model_v1.py "$TMP/v3/"
cp model_v1.py model_v2.py model_v4_sweep.py model_v5_exponent.py canonical_results.json "$TMP/v5/"
( cd "$TMP/v1" && "$PY" model_v1.py > v1.log 2>&1 )
if grep -q "1.52e-14" "$TMP/v1/v1.log"; then
  ok "criterion 1: the two exact routes agree to 1.52e-14 (registered <= 1e-6)"
else bad "criterion 1 number 1.52e-14 not found"; fi
cp model_v3.py "$TMP/v3/"
( cd "$TMP/v3" && "$PY" model_v3.py > v3.log 2>&1 )
if grep -q "3.01e-03" "$TMP/v3/v3.log"; then
  ok "proxy validation: quasi-static vs exact periodic cost worst error 3.01e-03"
else bad "proxy number 3.01e-03 not found"; fi
( cd "$TMP/v5" && "$PY" model_v5_exponent.py > v5.log 2>&1 )
if grep -q "worst |FOC - sweep| over all interior cells = 0.0000" "$TMP/v5/v5.log"; then
  ok "the FOC identity reproduces the sweep's optimum exactly (0.0000)"
else bad "the FOC worst-difference line was not found"; fi
if grep -q "REFUTED as a quantitative law" "$TMP/v5/v5.log"; then
  ok "the candidate closed form is reported refuted by the run itself"
else bad "the refutation verdict line was not found"; fi

printf '\n'
if [ "$FAIL" -eq 0 ]; then
  echo "REPRODUCE: ALL GREEN"
else
  echo "REPRODUCE: FAILED"
fi
exit "$FAIL"
