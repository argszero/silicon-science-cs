#!/usr/bin/env bash
#
# Issue #44 -- one-command reproduction.
#
#     bash reproduce.sh
#
# Step 1 runs the five stage instruments in the order the claims require (instrument_v4.py
# reads the artefact instrument_v3.py writes), then rebuilds `canonical_results.json` and
# `run.log`, recomputing every registered criterion, every sensitivity statement and the
# `manuscript_facts` block from the stage artefacts' primitives, and cross-checking each
# against the flag the stage recorded about itself.
#
# Step 2 regenerates the six figures and re-verifies them: that the committed manifest is
# the manifest a fresh run produces, that every label a caption promises is actually drawn,
# and that every positioned element falls inside the rendered canvas.
#
# Step 3 reassembles `manuscript.md` from its part files and checks it: that a fresh
# assembly from a foreign working directory is byte-identical to the committed manuscript,
# that the numbers in the prose really come out of the artefact (a mutation control changes
# one fact and requires the prose to change, and a deleted fact must be fatal rather than
# silent), that every cited key has a reference entry and every entry is cited, that the
# reference count clears the journal's bar, that every entry carries an authenticity record
# in `reference-check.md`, and that tables and figures are numbered, embedded, captioned and
# cited in the text.
#
# EXPECTED OUTPUT (the verdict lines, in this order):
#
#     criteria: a=MET, b=MET, c=MET, d=MET
#     cross-checks: <n> run, 0 failed                         (n = 85 at the time of writing)
#     canonical_results.json sha256 <digest>
#     figure checks: <n> run, 0 failed                        (n = 106 at the time of writing)
#     assemble: <n> placeholders resolved, <m> references cited
#     manuscript check: <n> run, 0 failed
#     verdict: OK
#     REPRODUCE: ALL GREEN
#
# The digests and the counts are printed, not asserted against a literal: a number this
# script cannot re-derive is a number it must not quote.  Run it twice and diff the two
# outputs -- everything except the figure pixel hashes must be identical.
#
# EXIT STATUS carries the verdict: 0 only if every check passes; any disagreement names the
# check that disagrees.
#
# DEPENDENCIES.  The instruments, the runner and the manuscript tools are pure Python
# standard library -- no numpy, no scipy, no network.  Only the figures need matplotlib, so
# a machine without it still reproduces every number and the whole manuscript (steps 1 and
# 3) and reports that step 2 was skipped.  Set REQUIRE_FIGURES=1 to make a missing
# matplotlib fatal.  Override the interpreters with PYTHON=... and PYTHON_FIGURES=...
#
# THE BIBLIOGRAPHY IS NOT RE-VERIFIED HERE.  `verify_refs.sh` re-queries Crossref and arXiv
# for all 102 keys and rewrites `references.md` and `reference-check.md`; it needs network
# access and is run deliberately, not on every reproduction.  The submission's bibliography
# is the output of that run, and every row of `reference-check.md` records which lookup
# produced it.
#
# DETERMINISM.  Nothing written by steps 1 and 3 contains a wall-clock, a host name or an
# absolute path, and `canonical_results.json`, `run.log` and `manuscript.md` are
# byte-identical across runs and across working directories.  The stage artefacts are
# byte-identical too.  The PNGs are a different matter: their bytes depend on the matplotlib
# build, so each figure's manifest entry records the build that produced it and pins the
# DATA (a digest over both the declared arrays and the numbers read back off the drawn
# artists).  Reproduce on a different build and the data digests still have to match
# exactly; the pixel hashes are then reported rather than required.
#
# RUNTIME: about 90 s for step 1, about 30 s for step 2, a few seconds for step 3, on one
# CPU core.

set -euo pipefail

here="$(cd "$(dirname "$0")" && pwd)"
cd "$here"

pick_python() {
  for c in "${PYTHON:-}" python3 /usr/bin/python3 /usr/local/bin/python3; do
    [ -n "$c" ] || continue
    if command -v "$c" > /dev/null 2>&1; then echo "$c"; return 0; fi
  done
  return 1
}

pick_figure_python() {
  for c in "${PYTHON_FIGURES:-}" /usr/bin/python3 python3 /usr/local/bin/python3; do
    [ -n "$c" ] || continue
    if command -v "$c" > /dev/null 2>&1 && "$c" -c "import matplotlib" > /dev/null 2>&1; then
      echo "$c"; return 0
    fi
  done
  return 1
}

PY="$(pick_python)" || { echo "FATAL: no python3 found."; exit 1; }
echo "interpreter: $PY ($("$PY" -c 'import sys; print(sys.version.split()[0])'))"

echo
echo "== 1. stages and the canonical aggregate =="
"$PY" canonical_runner.py

echo
echo "== 2. figures =="
FPY="$(pick_figure_python)" || FPY=""
if [ -n "$FPY" ]; then
  echo "figure interpreter: $FPY ($("$FPY" -c 'import matplotlib; print("matplotlib " + matplotlib.__version__)'))"
  "$FPY" verify_figures.py
else
  echo "SKIPPED: no interpreter with matplotlib was found, so the figures were not rebuilt."
  echo "         Every NUMBER in this package was still reproduced by step 1."
  echo "         Hint: python3 -m pip install --user matplotlib   or set PYTHON_FIGURES=..."
  if [ "${REQUIRE_FIGURES:-0}" = "1" ]; then
    echo "FATAL: REQUIRE_FIGURES=1 and matplotlib is missing."
    exit 1
  fi
fi

echo
echo "== 3. manuscript =="
"$PY" assemble.py
"$PY" check_manuscript.py

echo
echo "REPRODUCE: ALL GREEN"
