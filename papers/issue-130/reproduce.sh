#!/usr/bin/env bash
# reproduce.sh -- issue #130, "A Threshold Is Not a Measurement"
#
# WHAT THIS RECOMPUTES (not a checksum check over committed outputs): it re-runs the ten experiments
# from their own code over the committed corpus and compares each fresh report BYTE-FOR-BYTE against
# the report the package ships, then re-runs the analysis that derives the paper's tables from those
# reports, then runs the determinism certificate's own battery. Every number in the manuscript is read
# off one of these artefacts.
#
# RUN IT FROM THE PACKAGE DIRECTORY:   cd papers/issue-130 && bash reproduce.sh
# ENVIRONMENT: CPython 3.9 (measured on 3.9.6, macOS) -- the instruments are pure standard library plus
#   `math`/`random`/`hashlib`; NO third-party dependency is imported, so there is no library version
#   whose arithmetic enters a comparison. Override the interpreter with PYTHON=/path/to/python3.
# INPUTS: corpus/pg*.txt, committed in the package (8 Project Gutenberg texts, 5.6 MB), verified against
#   corpus/SHA256SUMS at the start of every run. corpus/fetch_corpus.sh re-obtains them from the network;
#   it is NOT needed to reproduce, and this run never touches the network.
# TOLERANCE: exact -- the comparison is sha256 equality against the shipped reports. (A second machine
#   under another build of the same interpreter can differ in set-iteration order or rounding; that is
#   what the value is, so it is stated rather than widened.)
# WHAT IT WRITES: nothing inside the package. The instruments emit their reports into a private temp
#   directory this script creates and removes. (`spike_v7.py` reads the package's
#   `spike_v4_results.json` on purpose -- its certificate X1 asserts its pools ARE that report's pools.)
# COST: about 4 minutes (the ten instruments; spike_v4 and spike_v5 are ~95 s and ~89 s).
#
# SECOND TIER (opt-in, about 13 minutes more):  REPRO_FULL=1 bash reproduce.sh
#   runs repro_check.py, which re-runs every instrument TWICE in separate processes and compares the two
#   artefacts -- the determinism certificate. It rewrites `artefact_hashes.json` in place (the one file
#   this package's run may write); the last step then compares the regenerated table against the shipped
#   one and restores the shipped copy, so the committed file is what stays on disk.

set -u
PY="${PYTHON:-python3}"
HERE="$(cd "$(dirname "$0")" && pwd)"
cd "$HERE"
WORK="$(mktemp -d "${TMPDIR:-/tmp}/issue130-repro.XXXXXX")"
trap 'rm -rf "$WORK"' EXIT
FAILED=0

say()  { printf '%-14s %s\n' "$1" "$2"; }
bad()  { printf '%-14s FAILED -- %s\n' "$1" "$2"; FAILED=$((FAILED+1)); }
run()  { local s="$1"; shift; ( cd "$WORK" && "$PY" "$HERE/$s" "$@" ); }
need() { if printf '%s' "$2" | grep -qE "$3"; then say "$1" "$4"; else bad "$1" "$4 (expected /$3/)"; fi; }

echo "== #130 reproduction =="

# ---- 0. the build -----------------------------------------------------------------------------------------
BUILD=$("$PY" -c 'import sys;print(sys.executable, sys.version.split()[0])' 2>/dev/null) \
  || { echo "no interpreter at '$PY' -- set PYTHON=/path/to/python3"; exit 2; }
say "build" "$BUILD | stdlib only (no third-party import anywhere in the package)"

# ---- 1. the corpus is the pinned one ----------------------------------------------------------------------
if command -v shasum >/dev/null 2>&1; then SUMS=$(cd corpus && shasum -a 256 -c SHA256SUMS 2>&1); else
  SUMS=$(cd corpus && sha256sum -c SHA256SUMS 2>&1); fi
NOK=$(printf '%s' "$SUMS" | grep -c 'OK$'); NFAIL=$(printf '%s' "$SUMS" | grep -c 'FAILED')
if [ "$NOK" = "8" ] && [ "$NFAIL" = "0" ]; then say "corpus" "8 file(s) verified against corpus/SHA256SUMS"
else bad "corpus" "$NOK file(s) OK, $NFAIL FAILED -- the pinned corpus is not the one this package was measured on"; fi

# ---- 2. the ten instruments reproduce the shipped reports -------------------------------------------------
NM=0; NT=0
for name in spike_v0 spike_v1 spike_v2 spike_v3 spike_v4 spike_v5 spike_v6 spike_v7 floor_v2 floor_v3; do
  NT=$((NT+1))
  if ! run "$name.py" > "$WORK/$name.stdout" 2>&1; then
    bad "instruments" "$name.py exited non-zero -- $(tail -1 "$WORK/$name.stdout")"; continue
  fi
  GOT=$("$PY" -c 'import hashlib,sys,io;print(hashlib.sha256(io.open(sys.argv[1],"rb").read()).hexdigest())' "$WORK/${name}_results.json")
  WANT=$("$PY" -c 'import json,sys;print(json.load(open(sys.argv[1]))["instrument_hashes"][sys.argv[2]]["sha256"])' artefact_hashes.json "$name")
  if [ "$GOT" = "$WANT" ]; then NM=$((NM+1)); printf '  %-9s MATCH  %s\n' "$name" "$(printf '%s' "$GOT" | cut -c1-16)"
  else bad "instruments" "$name produced $(printf '%s' "$GOT" | cut -c1-16) but the package ships $(printf '%s' "$WANT" | cut -c1-16)"; fi
done
if [ "$NM" = "10" ] && [ "$NT" = "10" ]; then say "instruments" "$NM of $NT reports re-run byte-identically"; else bad "instruments" "$NM of $NT reports matched"; fi

# ---- 3. the analysis, and its certificate -----------------------------------------------------------------
A2=$(run analyse_v2.py); rc=$?
if [ "$rc" != "0" ]; then bad "analysis" "analyse_v2.py exited $rc"; else
  NTB=$(printf '%s' "$A2" | grep -c '^TABLE ')
  need analysis "$A2" "^TABLE 1 -- the null population is LENGTH-DEPENDENT" "re-derived its tables ($NTB of 6 printed)"
  need analysis "$A2" "certificate: 21 cells, worst \|diff\| = 0.035" "the mechanism certificate (predicted vs measured eps*)"
  need analysis "$A2" "dice2c  rate   slope=-0.230  \(n=7, R2=0.950\)" "the boundary power law (slope -0.230, R2 0.950)"
fi

# ---- 4. the determinism certificate can fail --------------------------------------------------------------
RS=$(run repro_check.py --selftest); rc=$?
if [ "$rc" != "0" ]; then bad "certificate" "repro_check.py --selftest exited $rc"; else
  need certificate "$RS" "P1 identical objects -> PASS" "plant 1: identical objects must NOT fire"
  need certificate "$RS" "P2 one byte differs -> FAIL" "plant 2: a one-byte change MUST fire"
  need certificate "$RS" "P3 hash\(str\)-seeded processes -> FAIL" "plant 3: the real cross-process defect MUST fire"
fi

# ---- 5. opt-in: the two-run determinism certificate --------------------------------------------------------
if [ "${REPRO_FULL:-0}" = "1" ]; then
  cp artefact_hashes.json "$WORK/shipped_hashes.json"
  RF=$(run repro_check.py); rc=$?
  if [ "$rc" != "0" ]; then bad "determinism" "repro_check.py exited $rc"; else
    need determinism "$RF" "DETERMINISM CERTIFICATE: ALL PASS  \(10/10" "10 of 10 instruments reproduce byte-for-byte over two runs"
  fi
  if "$PY" -c 'import json,sys
a=json.load(open(sys.argv[1]))["instrument_hashes"]; b=json.load(open(sys.argv[2]))["instrument_hashes"]
sys.exit(0 if a==b else 1)' artefact_hashes.json "$WORK/shipped_hashes.json"; then
    say determinism "the regenerated table equals the shipped artefact_hashes.json"
  else bad "determinism" "the regenerated artefact_hashes.json differs from the shipped one"; fi
  cp "$WORK/shipped_hashes.json" artefact_hashes.json   # leave the committed file as committed
else
  say "determinism" "skipped -- REPRO_FULL=1 adds the two-run certificate (~13 min)"
fi

echo
if [ "$FAILED" = "0" ]; then echo "REPRODUCE: ALL GREEN"; exit 0; fi
echo "REPRODUCE: $FAILED CHECK(S) FAILED"; exit 1
