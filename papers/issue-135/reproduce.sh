#!/usr/bin/env bash
# reproduce.sh -- issue #135, "The Load Factor Is Not the Tail"
#
# WHAT THIS RECOMPUTES (not a checksum check over committed outputs): it re-runs the FOUR
# instruments from their own code and compares each fresh report BYTE-FOR-BYTE against the report
# this package ships, after running each instrument's own plant battery.  Every number that will
# appear in the manuscript is read off one of these reports.
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
# COST: about four minutes (four instruments, each re-run once; the plant batteries add ~20 s).
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

echo
if [ "$FAILED" = "0" ]; then echo "REPRODUCE: ALL GREEN"; else echo "REPRODUCE: $FAILED step(s) FAILED"; fi
exit "$FAILED"
