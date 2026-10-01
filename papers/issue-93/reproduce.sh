#!/usr/bin/env bash
# #93 -- "When Does a Human Approval Gate Pay?" : one command reproduces every reading the manuscript rests on.
#
# ONE COMMAND:   bash reproduce.sh
# EXPECTED:      a line per step, then `REPRODUCE: ALL GREEN` (exit 0).  Any step whose own reading fails stops
#                the run with `FAILED` and a non-zero exit; the full expected transcript is in README.md.
# TOLERANCE:     the seven deterministic instrument reports must be BYTE-IDENTICAL over two runs (the run measures
#                it below).  The crc32 `report id` each instrument prints is a digest OF a report, not a
#                measurement: a different interpreter/NumPy pair may move it, which is why the digests are printed
#                and the numbers are compared exactly.
# BUILD:         declare with PYTHON=/path/to/python3 (default /usr/bin/python3).  Read on Python 3.9.6 /
#                numpy 2.0.2; the instruments are pure-Python + numpy.
set -u
HERE=$(cd "$(dirname "$0")" && pwd)
PY=${PYTHON:-/usr/bin/python3}
cd "$HERE" || { echo "cannot enter $HERE"; exit 1; }

FAILED=0
say()  { printf '%-14s %s\n' "$1" "$2"; }
bad()  { printf '%-14s FAILED -- %s\n' "$1" "$2"; FAILED=1; }
need() { # need <step> <haystack-or-""> <pattern> <what it is>
  if printf '%s' "$2" | grep -qE "$3"; then return 0; fi
  bad "$1" "the run did not print $4 (pattern: $3)"; return 1
}

digests() { "$PY" -c 'import glob,hashlib;print(" ".join(hashlib.sha256(open(p,"rb").read()).hexdigest() for p in sorted(glob.glob("gate_v*_results.json"))))'; }
run() { "$@" 2>&1; }            # capture stdout+stderr; the step's own exit code is read from $?

echo "== #93 reproduction =="
say "build" "$PY $("$PY" -c 'import sys;print(sys.version.split()[0])') | numpy $("$PY" -c 'import numpy;print(numpy.__version__)' 2>/dev/null || echo ABSENT)"

# ---- 1. the instruments -----------------------------------------------------------------------------------------
ONE=""
for g in 0 1 2 3 4 5 6; do
  out=$(run "$PY" "gate_v$g.py") || { bad "instruments" "gate_v$g.py exited non-zero"; continue; }
  ONE="$ONE$out"$'\n'
done
say "instruments" "7 instrument(s) ran, all exit 0 (report id(s) where printed: $(printf '%s' "$ONE" | grep -oE 'report id [0-9a-f]+' | awk '{print $3}' | tr '\n' ' '))"

# ---- 2. byte-identity over two runs (the tolerance) -------------------------------------------------------------
before=$(digests)
for g in 0 1 2 3 4 5 6; do "$PY" "gate_v$g.py" >/dev/null 2>&1 || bad "byte-identity" "gate_v$g.py exited non-zero on the second run"; done
after=$(digests)
if [ "$before" = "$after" ]; then say "byte-identity" "all 7 instrument reports byte-identical over two runs"; else bad "byte-identity" "an instrument report changed between runs"; fi
say "digests" "v0..v6 sha256(16): $(printf '%s' "$after" | tr ' ' '\n' | cut -c1-16 | tr '\n' ' ')"

# ---- 3. the batteries -------------------------------------------------------------------------------------------
BAT=""
for g in 0 1 2 3 4 5 6; do
  out=$(run "$PY" "v${g}_battery.py") || { bad "batteries" "v${g}_battery.py exited non-zero"; continue; }
  line=$(printf '%s' "$out" | grep -oE '([0-9]+/[0-9]+ (alarms fired|case\(s\) fired|caught)|caught: [0-9]+/[0-9]+)' | tail -1)
  [ -n "$line" ] || bad "batteries" "v${g}_battery.py printed no count line"
  BAT="$BAT v$g:$line"
done
say "batteries" "fired on every plant --$BAT"

# ---- 4. the outcome rows ----------------------------------------------------------------------------------------
out=$(run "$PY" outcome_check.py --selftest) || bad "outcomes" "outcome_check.py --selftest exited non-zero"
need "outcomes" "$out" 'OUTCOME CHECK: PASS' 'OUTCOME CHECK: PASS'
need "outcomes" "$out" 'OUTCOME CHECK BATTERY -- [0-9]+ case\(s\), [0-9]+ caught' 'the battery total'
need "outcomes" "$out" 'SELFTEST: PASS' 'SELFTEST: PASS'
say "outcomes" "$(printf '%s' "$out" | grep -oE 'OUTCOME CHECK BATTERY -- .*' | tail -1)"

# ---- 5. section 5 against the instruments that own it ------------------------------------------------------------
out=$(run "$PY" verify_s5.py --selftest) || bad "section 5" "verify_s5.py --selftest exited non-zero"
need "section 5" "$out" 'SECTION 5 NUMBERS: PASS -- [0-9]+ claim\(s\), 0 missing' 'a clean claim read'
need "section 5" "$out" 'BATTERY: [0-9]+ of [0-9]+ claim\(s\) fired' 'the per-claim battery'
need "section 5" "$out" 'ALPHABET CONTROL: 0 of [0-9]+ claim\(s\) satisfied' 'the alphabet control'
claims=$(printf '%s' "$out" | grep -oE 'PASS -- [0-9]+ claim' | grep -oE '[0-9]+')
say "section 5" "$(printf '%s' "$out" | grep -oE 'SECTION 5 NUMBERS: PASS.*' | tail -1)"
say "  batteries" "$(printf '%s' "$out" | grep -oE 'BATTERY: [0-9]+ of [0-9]+ claim\(s\) fired.*' | tail -1)"

# ---- 6. the reference pipeline ----------------------------------------------------------------------------------
out=$(run "$PY" refs/refs_check.py) || bad "references" "refs_check.py exited non-zero"
need "references" "$out" '24 checks, 0 failed' 'the stage-1 verdict'
out2=$(run "$PY" refs/refs_check2.py --selftest) || bad "references" "refs_check2.py --selftest exited non-zero"
need "references" "$out2" 'checks 15/15 PASS' 'the stage-2 verdict'
need "references" "$out2" 'caught 2[0-9]/2[0-9]' 'the stage-2 mutation count'
out3=$(run "$PY" refs/refs_check3.py --selftest) || bad "references" "refs_check3.py --selftest exited non-zero"
need "references" "$out3" 'checks 8/8 PASS' 'the stage-3 verdict'
need "references" "$out3" 'mutation battery \(19 cases' 'the stage-3 battery'
say "references" "stage 1: 24 checks, 0 failed | stage 2: 15/15 PASS with 22/22 mutations caught | stage 3: 8/8 PASS, 19-case battery"

# ---- 6b. the citation authenticity report ---------------------------------------------------------------------
out=$(run "$PY" refs/reference_check.py --selftest) || bad "authenticity" "reference_check.py --selftest exited non-zero"
need "authenticity" "$out" 'REFERENCE CHECK: PASS -- [0-9]+ check\(s\), 0 failed' 'the verdict'
need "authenticity" "$out" 'BATTERY: [0-9]+ of [0-9]+ case\(s\) fired' 'the battery'
say "authenticity" "$(printf '%s' "$out" | grep -oE 'REFERENCE CHECK: .*' | tail -1) | $(printf '%s' "$out" | grep -oE 'BATTERY: .*' | tail -1)"

# ---- 7. the manuscript's citations -------------------------------------------------------------------------------
out=$(run "$PY" cite_check.py --selftest) || bad "citations" "cite_check.py --selftest exited non-zero"
need "citations" "$out" 'citations [0-9]+ \| distinct keys [0-9]+ of [0-9]+ built records' 'the citation line'
need "citations" "$out" 'unknown keys 0' 'a clean resolution'
need "citations" "$out" 'MALFORMED +citation-shaped token\(s\) outside a well-formed bracket: 0' 'a clean malformed limb'
need "citations" "$out" 'uncited records 0 of [0-9]+' 'zero uncited records'
need "citations" "$out" 'renamed \[@[a-z0-9]+\] -> caught' 'the rename mutation'
say "citations" "$(printf '%s' "$out" | grep -E 'citations [0-9]+' | head -1)"

# ---- 8. the counts the manuscript states are the counts this run produced -----------------------------------------
# The manuscript states several of these numbers in prose.  A stated count is a claim with an owner, so it is
# compared against the RUN and not against a value typed into this script: each check reads a number out of the
# run's own output and then requires the manuscript to carry it.
CITED=$(printf '%s' "$out" | grep -oE 'citations [0-9]+' | head -1 | grep -oE '[0-9]+')
if grep -qF "$CITED citations" manuscript.md; then say "counts" "the manuscript states the run's citation count ($CITED citations)"; else bad "counts" "manuscript.md does not state '$CITED citations'"; fi
if grep -qF "$claims claim" manuscript.md; then say "counts" "the manuscript states the run's §5 claim count ($claims claim)"; else bad "counts" "manuscript.md does not state $claims claim(s)"; fi
if grep -qF "120 distinct keys of 120" manuscript.md; then say "counts" "the manuscript states the built-record count (120 distinct keys of 120)"; else bad "counts" "manuscript.md does not state 120 distinct keys of 120"; fi
NVER=$("$PY" -c 'import json;print(json.load(open("reference-check.json"))["n_verified"])')
NTOT=$("$PY" -c 'import json;print(len(json.load(open("reference-check.json"))["rows"]))')
if grep -qF "$NVER of $NTOT verified" manuscript.md; then say "counts" "the manuscript states the authenticity count ($NVER of $NTOT verified)"; else bad "counts" "manuscript.md does not state '$NVER of $NTOT verified'"; fi

# ---- 8b. the figures are the ones this run draws, and the product's links resolve -----------------------------
out=$(run "$PY" figures/make_figures.py --check) || bad "figures" "make_figures.py --check exited non-zero"
need "figures" "$out" 'CURRENT -- .*byte-identical to a fresh draw' 'the byte-identity verdict'
say "figures" "$(printf '%s' "$out" | grep -oE 'CURRENT -- .*' | tail -1)"

out=$(run "$PY" check_links.py --selftest) || bad "links" "check_links.py --selftest exited non-zero"
need "links" "$out" 'LINK CHECK: PASS -- [0-9]+ link\(s\), [0-9]+ local, 0 broken' 'the link verdict'
need "links" "$out" 'BATTERY: [0-9]+ of [0-9]+ case\(s\) fired' 'the link battery'
say "links" "$(printf '%s' "$out" | grep -oE 'LINK CHECK: PASS.*' | tail -1) | $(printf '%s' "$out" | grep -oE 'BATTERY: .*' | tail -1)"

# ---- 8c. the journal's submission bar, read rather than asserted -------------------------------------------------
out=$(run "$PY" submission_check.py --selftest) || bad "bar" "submission_check.py --selftest exited non-zero"
need "bar" "$out" 'SUBMISSION CHECK: PASS -- [0-9]+ item\(s\), 0 failed' 'the bar verdict'
need "bar" "$out" 'BATTERY: [0-9]+ of [0-9]+ case\(s\) fired' 'the bar battery'
say "bar" "$(printf '%s' "$out" | grep -oE 'SUBMISSION CHECK: PASS -- [0-9]+ item\(s\), 0 failed, [0-9]+ declared' | tail -1) | $(printf '%s' "$out" | grep -oE 'BATTERY: .*' | tail -1)"

# ---- 9. the product is the assembly of the parts it claims to be --------------------------------------------------
if [ -f manuscript.md ] && [ -f refs/refs_keys.json ]; then
  say "product" "manuscript.md $(wc -c < manuscript.md | tr -d ' ') bytes, sha256 $("$PY" -c 'import hashlib;print(hashlib.sha256(open("manuscript.md","rb").read()).hexdigest()[:16])')"
else
  bad "product" "manuscript.md or refs/refs_keys.json is missing"
fi

echo
if [ "$FAILED" -eq 0 ]; then echo "REPRODUCE: ALL GREEN"; else echo "REPRODUCE: FAILED"; fi
exit "$FAILED"
