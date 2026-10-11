#!/usr/bin/env bash
# reproduce.sh -- issue #135, "The Load Factor Is Not the Tail"
#
# WHAT THIS RECOMPUTES (not a checksum check over committed outputs): it re-runs the FOUR
# instruments from their own code and compares each fresh report BYTE-FOR-BYTE against the report
# this package ships, after running each instrument's own plant battery; it then regenerates the
# FIGURE SET from those reports and compares all nine figure files byte-for-byte; and it checks the
# REFERENCE LAYER offline -- the refscan plant battery, the pool gate (which binds the committed
# verification receipt to the shipped pool by sha256), and the receipt rendering.  Every number that
# will appear in the manuscript is read off one of these reports, every figure from them, and every
# reference from the verified pool.
#
# RUN IT FROM THE PACKAGE DIRECTORY:   cd papers/issue-135 && bash reproduce.sh
# ENVIRONMENT: CPython 3 (measured on 3.12.12 and 3.13.9, macOS) -- the instruments are pure
#   standard library (`json`/`math`/`os`/`sys`); NO third-party dependency is imported, so no library
#   version enters a comparison.  Override the interpreter with PYTHON=/path/to/python3.
# INPUTS: none.  Every key set is generated from the committed SplitMix64 seeds inside the
#   instruments, so this run never touches the network and needs no corpus.
# TOLERANCE: exact -- the comparison is byte equality against the shipped reports.
# WHAT IT WRITES: nothing inside the package.  Each instrument is run with SPIKE_OUT pointing into a
#   private temp directory this script creates and removes.
# COST: about five minutes (four instruments, each re-run once; the plant batteries, the figure
#   certificate and the offline reference layer add ~50 s).  The LIVE reference verification
#   (`refscan135.py --verify`) is a separate network pass and is NOT part of this offline run.
#
# SECOND TIER (opt-in):  REPRO_FULL=1 bash reproduce.sh
#   re-runs every instrument a SECOND time in a fresh process and compares the two fresh artefacts --
#   the determinism certificate.

set -u
PY="${PYTHON:-python3}"
HERE="$(cd "$(dirname "$0")" && pwd)"
cd "$HERE"
WORK="$(mktemp -d "${TMPDIR:-/tmp}/issue135-repro.XXXXXX")"
trap 'rm -rf "$WORK"' EXIT
FAILED=0

say()  { printf '%-18s %s\n' "$1" "$2"; }
bad()  { printf '%-18s FAILED -- %s\n' "$1" "$2"; FAILED=$((FAILED+1)); }

echo "== #135 reproduction =="

# ---- 0. the build ------------------------------------------------------------------------------
BUILD=$("$PY" -c 'import sys;print(sys.executable, sys.version.split()[0])' 2>/dev/null) \
  || { echo "no interpreter at '$PY' -- set PYTHON=/path/to/python3"; exit 2; }
say "build" "$BUILD | stdlib only (no third-party import anywhere in the package)"

# ---- 1. each instrument: plants first, then a byte-for-byte reproduction -----------------------
for n in 0 1 2 3; do
  S="spike_v${n}.py"; R="spike_v${n}_results.json"
  if OUT=$("$PY" "$HERE/$S" --selftest 2>&1); then
    say "$S selftest" "$(printf '%s' "$OUT" | tail -1)"
  else
    bad "$S selftest" "the plant battery failed"
  fi
  ( cd "$WORK" && SPIKE_OUT="$WORK/$R" "$PY" "$HERE/$S" >/dev/null 2>&1 ) \
    || { bad "$S run" "the instrument did not complete"; continue; }
  if cmp -s "$WORK/$R" "$HERE/$R"; then
    say "$S report" "byte-identical to the shipped $R ($(shasum -a 256 "$HERE/$R" | cut -c1-16))"
  else
    bad "$S report" "$R differs from the shipped report"
  fi
done

# ---- 2. second tier: the determinism certificate ------------------------------------------------
if [ "${REPRO_FULL:-0}" = "1" ]; then
  for n in 0 1 2 3; do
    R="spike_v${n}_results.json"
    ( cd "$WORK" && SPIKE_OUT="$WORK/a_$R" "$PY" "$HERE/spike_v${n}.py" >/dev/null 2>&1 )
    ( cd "$WORK" && SPIKE_OUT="$WORK/b_$R" "$PY" "$HERE/spike_v${n}.py" >/dev/null 2>&1 )
    if cmp -s "$WORK/a_$R" "$WORK/b_$R" && cmp -s "$WORK/a_$R" "$HERE/$R"; then
      say "determinism v${n}" "two fresh runs byte-identical, and equal to the shipped report"
    else
      bad "determinism v${n}" "a fresh run differs"
    fi
  done
fi

# ---- 3. the figure set: the certificate, then a byte-for-byte regeneration ----------------------
FIGFILES="fig1_budget_boundary.svg fig2_scheme_deviation.svg fig3_finite_size.svg \
fig4_tail_decay.svg fig5_closed_forms.svg fig6_clustering_vs_tail.svg FIGURES.md CAPTIONS.md manifest.json"
if OUT=$("$PY" "$HERE/make_figures.py" --selftest 2>&1); then
  say "make_figures" "$(printf '%s' "$OUT" | tail -1) (F1-F5)"
else
  bad "make_figures" "the figure certificate failed"
  printf '%s\n' "$OUT" | sed 's/^/                   /'
fi
mkdir -p "$WORK/figures"
if "$PY" "$HERE/make_figures.py" "$WORK/figures" >/dev/null 2>&1; then
  FIGOK=1
  for f in $FIGFILES; do
    cmp -s "$WORK/figures/$f" "$HERE/figures/$f" || { FIGOK=0; bad "figure $f" "differs from the shipped file"; }
  done
  [ "$FIGOK" = "1" ] && say "figures" "9 files byte-identical to the shipped figure set"
else
  bad "make_figures run" "the generator did not complete (a figure left its axes?)"
fi

# ---- 4. the reference layer: plant battery, OFFLINE gate, receipt rendering --------------------
# The live network verification (`refscan135.py --verify`) is a separate, documented pass; its
# verbatim output is the committed receipt refs/verify-run.txt, which the gate below binds to the
# shipped pool by sha256 -- so this step is OFFLINE and still checks that the receipt is current.
if OUT=$("$PY" "$HERE/refscan135.py" --selftest 2>&1); then
  say "refscan selftest" "$(printf '%s' "$OUT" | tail -1)"
else
  bad "refscan selftest" "the plant battery failed"
fi
if OUT=$("$PY" "$HERE/refscan135.py" --gate 2>&1); then
  say "refscan gate" "$(printf '%s' "$OUT" | tail -1) -- live verification is in reference-check.md"
else
  bad "refscan gate" "the offline reference-pool gate failed"
  printf '%s\n' "$OUT" | sed 's/^/                   /'
fi
if OUT=$("$PY" "$HERE/make_reference_check.py" --check 2>&1); then
  say "reference-check" "$(printf '%s' "$OUT" | tail -1)"
else
  bad "reference-check" "$(printf '%s' "$OUT" | tail -1)"
fi
# the renderer's plant: a change INSIDE the generated block must make --check FAIL.  (A change
# OUTSIDE the markers is correctly preserved -- the renderer owns only the block -- so the plant
# targets the block itself, one digit of the receipt's verdict line.)
sed 's/VERIFIED 556 \/ 556/VERIFIED 999 \/ 999/' "$HERE/reference-check.md" > "$WORK/reference-check.md"
if ! grep -q 'VERIFIED 999' "$WORK/reference-check.md"; then
  bad "reference-check plant" "the plant did not land in the block (the receipt line moved?)"
elif "$PY" "$HERE/make_reference_check.py" --check "$WORK/reference-check.md" >/dev/null 2>&1; then
  bad "reference-check plant" "a planted change did NOT make --check fail"
else
  say "reference-check plant" "a planted change inside the block makes --check fail"
fi

echo
if [ "$FAILED" = "0" ]; then echo "REPRODUCE: ALL GREEN"; else echo "REPRODUCE: $FAILED step(s) FAILED"; fi
exit "$FAILED"
