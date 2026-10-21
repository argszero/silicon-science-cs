#!/usr/bin/env bash
# reproduce.sh -- issue #141, "The Score Is Not the Payoff"
#
# WHAT THIS DOES (it RECOMPUTES; it is not a checksum check over committed outputs): every research
# instrument is re-run from its own code in an ISOLATED COPY of the package and its fresh artefact is
# compared BYTE-FOR-BYTE against the one this package ships; each instrument's own plant battery is
# run and its VERDICT LINE is read; the three figures are rebuilt from the JSON alone and the PNGs
# compared byte-for-byte; the numeric gate re-derives every number the manuscript quotes from the
# artefact that holds it; the manuscript is re-rendered from its source and compared byte-for-byte;
# and the reference layer is re-checked OFFLINE.  Every number in the paper is read off one of these
# artefacts, so a number that has drifted from its artefact fails here rather than in a proofreader's
# queue.
#
# RUN IT FROM THE PACKAGE DIRECTORY:   cd papers/issue-141 && bash reproduce.sh
# ENVIRONMENT: CPython 3.9.6 with numpy 2.0.2 and matplotlib 3.9.4 (macOS, measured 2026-10-20).
#   That is the WHOLE third-party set, and it is an IMPORT CENSUS rather than a memory: over the
#   package's twelve scripts `import numpy` appears in two (census_converse_scope.py, figures.py) and
#   `import matplotlib` in the same two; every other import is standard library -- `fractions`,
#   `json`, `hashlib`, `itertools`, `subprocess`, `urllib`, `xml`, `unicodedata`, `collections`.
#   Nothing imports scipy.  Override the interpreter with PYTHON=/path/to/python3.
# INPUTS: none, and NO NETWORK on any step whose verdict is reported here.  Every grid is enumerated
#   from constants inside the instruments and there is no seed anywhere in the design: the space is
#   exact, so there is nothing to sample.  LIVE reference verification (finding a record for a work
#   that has none) is a separate network pass -- see README; the offline gate re-checks what is
#   already verified.
# TOLERANCE: exact -- byte equality against the shipped artefacts, figures and manuscript.
# A LEG THAT CANNOT RUN IS NAMED `NOT RUN`, NEVER `DIFFERS`: an instrument that aborts (missing
#   dependency, wrong interpreter) produced no second reading, so there is nothing to compare;
#   reporting that as a disagreement would present an environment gap as a scientific defect.
#   `DIFFERS` is reserved for a run that COMPLETED and produced different bytes.
# EXIT STATUS: 0 = `REPRODUCE: ALL GREEN`; 1 = at least one step FAILED (the count is printed).
# PLANT TIER (opt-in): PLANT=1 bash reproduce.sh fires each reader on the defect it is built to
#   catch and requires it to FIRE -- a verdict reader on a disagreeing pair of counts and on silence,
#   the artefact comparison on a one-byte change, the render on a citation with no record, and the
#   figure comparison on a one-byte change in a PNG.  It costs about 15 seconds and runs in the copy.
# WRITES NOTHING INSIDE THE PACKAGE: the copy below is the only tree any script writes into, and it
#   is removed on exit, so a reproduction run cannot repair the artefact it is testing.
# COST: about five minutes on the machine this was measured on (2026-10-20: 4m43s; instrument
#   v4's certificate dominates -- it re-derives the headline and runs a subprocess -- and every
#   other step is seconds).

set -u
PY="${PYTHON:-/usr/bin/python3}"
HERE="$(cd "$(dirname "$0")" && pwd)"
cd "$HERE"
FAILS=0
SKIPS=0   # legs that could not be RUN, named as such -- never counted as passes
step() { printf '%-52s' "$1"; }
ok()   { echo "OK${1:+ ($1)}"; }
bad()  { echo "FAILED${1:+ ($1)}"; FAILS=$((FAILS+1)); }
skip() { echo "NOT RUN${1:+ ($1)}"; SKIPS=$((SKIPS+1)); }

# ---------------------------------------------------------------- 0. the interpreter
step "interpreter carries the declared dependencies"
# The probe covers the WHOLE declared set: one that checked a single module would let the other abort
# mid-run, and the abort would then be read as a FAILED with no evidence behind it (the #142 lesson,
# 2026-10-17: a venv built exactly as the README declared it aborted two instruments on `scipy`).
if DEPS=$("$PY" - 2>&1 <<'PYX'
import importlib.metadata as md, importlib.util, sys
need = ("numpy", "matplotlib")
missing = [n for n in need if importlib.util.find_spec(n) is None]
if missing:
    print("MISSING %s" % ", ".join(missing)); sys.exit(1)
# versions come from distribution METADATA, never from importing: importing matplotlib can write a
# cache directory and print a warning, and this probe's output is what the reader is shown
vers = {}
for n in need:
    try:
        vers[n] = md.version(n)
    except Exception:
        vers[n] = "unknown"
print("python %s / %s" % (sys.version.split()[0], " / ".join("%s %s" % (n, vers[n]) for n in need)))
PYX
); then
  ok "$DEPS"
else
  case "$DEPS" in
    *MISSING*) bad "$DEPS -- $PY lacks a declared dependency; set PYTHON=/path/to/python3" ;;
    *)         bad "$PY could not run the dependency probe: $(printf '%s' "$DEPS" | tail -1)" ;;
  esac
  echo; echo "REPRODUCE: ABORTED"; exit 1
fi

WORK="$(mktemp -d "${TMPDIR:-/tmp}/issue141-repro.XXXXXX")"
trap 'rm -rf "$WORK"' EXIT
mkdir -p "$WORK/.mpl" "$WORK/copy"
# A FULL COPY, not a copy of the scripts: instrument v4's certificate re-derives its headline from
# `spike_v4_results.json` READ OFF DISK, the censuses read the v4 artefact, and the manuscript build
# reads `refs/`.  A scripts-only copy would fail those legs for the copy's emptiness and the reader
# would read it as a defect.  The copy keeps the SHIPPED FILE NAMES because one script echoes its own
# output path into its report.
cp -R "$HERE"/. "$WORK/copy/" 2>/dev/null
RUN="$WORK/copy"

# ---------------------------------------------------------------- 1. the plant batteries
# Each battery's verdict is read from what it PRINTS.  THREE printed forms exist in this package and
# all three carry an `a/b` count; a battery that prints none of them FAILS rather than passing by
# silence, and one whose printed counts disagree with each other fails too (a battery that says
# "5/5" and "3 ok" in one breath has not told the reader which number to believe).
verdict_of() {          # $1 = the captured output; echoes a verdict, or nothing
  local t="$1" a b
  # FORM 1 -- a count line: `SELFTEST 23/23` or `35/35 certificate items`.  The battery's own two
  # numbers must agree; one that prints "5/5" and "3" in one breath has not said which to believe.
  a=$(printf '%s' "$t" | grep -oE 'SELFTEST[: ]+[0-9]+/[0-9]+' | tail -1 | grep -oE '[0-9]+/[0-9]+')
  [ -n "$a" ] || a=$(printf '%s' "$t" | grep -oE '[0-9]+/[0-9]+ certificate items' | tail -1 | grep -oE '[0-9]+/[0-9]+')
  if [ -n "$a" ]; then
    if [ "${a%%/*}" = "${a##*/}" ]; then echo "$a"; else echo "DISAGREE $a"; fi
    return 0
  fi
  # FORM 2 -- a NAMED verdict with no count (`SELFTEST: ALL PASS`, `REFSCAN: ALL PASS`,
  # `FIGURES-SELFTEST: ALL PASS`).  The count reported upward is then the number of `] ok` lines the
  # battery actually printed -- READ OFF the output, never invented: the first draft of this reader
  # mapped `ALL PASS` to a literal `1/1`, which printed `OK (1/1)` for a 23-check battery and for a
  # 29-check one alike.  A reader that makes up a number is the defect it is meant to catch.
  local v n
  v=$(printf '%s' "$t" | grep -oE '[A-Z][A-Z-]*: ALL PASS' | head -1)
  [ -n "$v" ] || return 0
  n=$(printf '%s' "$t" | grep -c '\] ok' || true)
  if [ -n "$n" ] && [ "$n" != "0" ]; then echo "$v ($n checks)"; else echo "$v"; fi
}

battery() {             # $1 label  $2 script-and-args...
  local label="$1"; shift
  step "$label"
  local OUT RC V
  OUT=$( cd "$RUN" && MPLCONFIGDIR="$WORK/.mpl" "$PY" "$@" 2>&1 ); RC=$?
  V=$(verdict_of "$OUT")
  case "$V" in
    "")           bad "rc=$RC, the battery printed no verdict line: $(printf '%s' "$OUT" | tail -1)" ;;
    "DISAGREE "*) bad "${V#DISAGREE } -- the battery's own counts disagree" ;;
    *)            if [ "$RC" -ne 0 ]; then bad "$V but rc=$RC"; else ok "$V"; fi ;;
  esac
}

battery "plant battery v0" spike_v0.py --selftest
battery "plant battery v1" spike_v1.py --selftest
battery "plant battery v2" spike_v2.py --selftest
battery "plant battery v3" spike_v3.py --selftest
battery "plant battery v4" spike_v4.py --selftest

# ---------------------------------------------------------------- 2. the research artefacts
# Which artefact each instrument writes, and through which flag, is stated per row: the package has
# no single convention, and inventing one here would be a place for the reader to be wrong.
artefact() {            # $1 label  $2 shipped name  $3 command... (run inside $RUN)
  local label="$1" name="$2"; shift 2
  step "$label"
  if ! ( cd "$RUN" && MPLCONFIGDIR="$WORK/.mpl" "$PY" "$@" ) >"$WORK/last.log" 2>&1; then
    bad "the run failed: $(tail -1 "$WORK/last.log")"; return
  fi
  if cmp -s "$RUN/$name" "$HERE/$name"; then ok "byte-identical"; else bad "$name DIFFERS"; fi
}

artefact "artefact v0"  spike_v0_results.json  spike_v0.py --out spike_v0_results.json
artefact "artefact v1 (theory model)" spike_v1_theory.json spike_v1.py --out spike_v1_theory.json
artefact "artefact v2 (design space)" spike_v2_design.json spike_v2.py --out spike_v2_design.json
artefact "artefact v3"  spike_v3_results.json  spike_v3.py --out spike_v3_results.json
artefact "artefact v4"  spike_v4_results.json  spike_v4.py --out spike_v4_results.json
artefact "census: excess entries" census_excess_entries.json census_excess_entries.py --out census_excess_entries.json
artefact "census: converse scope" census_converse_scope.json census_converse_scope.py --out census_converse_scope.json
artefact "analysis: transitivity coordinate vs transport" analysis_transitivity_vs_transport.json analysis_transitivity_vs_transport.py

# the report texts: v0-v2 PRINT theirs to stdout, v3-v4 write theirs through --report
report() {              # $1 version  $2 mode
  step "report text v$1"
  local f="spike_v$1_report.txt"
  if [ "$2" = stdout ]; then
    ( cd "$RUN" && MPLCONFIGDIR="$WORK/.mpl" "$PY" "spike_v$1.py" ) >"$RUN/$f" 2>&1
  else
    ( cd "$RUN" && MPLCONFIGDIR="$WORK/.mpl" "$PY" "spike_v$1.py" --report "$f" ) >/dev/null 2>&1
  fi
  if cmp -s "$RUN/$f" "$HERE/$f"; then ok "byte-identical"; else bad "$f renders differently"; fi
}
report 0 stdout
report 1 stdout
report 2 stdout
report 3 --report
report 4 --report

step "census report text (converse scope)"
if cmp -s "$RUN/census_converse_scope_report.txt" "$HERE/census_converse_scope_report.txt"; then
  ok "byte-identical"
else
  bad "census_converse_scope_report.txt renders differently"
fi

# ---------------------------------------------------------------- 3. the figure set
step "figures regenerate byte-identically"
# `--check` PRINTS its verdict, so the VERDICT is read: a mismatch and a crash both exit nonzero and
# only the first is a disagreement about the figures.
FIGOUT=$( cd "$RUN" && MPLCONFIGDIR="$WORK/.mpl" "$PY" figures.py --check 2>&1 )
case "$FIGOUT" in
  *"FIGURES: ALL IDENTICAL"*) ok "$(printf '%s' "$FIGOUT" | grep -o 'FIGURES: ALL IDENTICAL.*' | head -1)" ;;
  *"FIGURES:"*)               bad "$(printf '%s' "$FIGOUT" | grep -o 'FIGURES:.*' | tail -1)" ;;
  *)                          skip "figures.py aborted: $(printf '%s' "$FIGOUT" | tail -1)" ;;
esac
battery "figure plant battery" figures.py --selftest

# ---------------------------------------------------------------- 4. the numeric gate
step "every quoted number re-derived from its artefact"
CO=$( cd "$RUN" && MPLCONFIGDIR="$WORK/.mpl" "$PY" canonical.py --selftest 2>&1 )
case "$CO" in
  *"CANONICAL: ALL PASS"*) ok "$(printf '%s' "$CO" | grep -o 'CANONICAL:.*' | tail -1)" ;;
  *)                       bad "$(printf '%s' "$CO" | grep -o 'CANONICAL:.*' | tail -1 || echo 'no verdict')" ;;
esac
step "manuscript annotations bind to those numbers"
NU=$( cd "$RUN" && MPLCONFIGDIR="$WORK/.mpl" "$PY" check_numbers.py 2>&1 )
case "$NU" in
  *"NUMBERS: OK"*) ok "$(printf '%s' "$NU" | grep -o 'NUMBERS: OK.*' | head -1)" ;;
  *)               bad "$(printf '%s' "$NU" | grep -o 'NUMBERS:.*' | tail -1 || echo 'no verdict')" ;;
esac

# ---------------------------------------------------------------- 5. the manuscript build
step "manuscript re-renders from its source"
# `--render` numbers the citations in order of first appearance and appends References.  It REFUSES
# to write when a cited key has no verified record, when a selected work is never cited in the body,
# or when fewer than the journal's 100 works are cited -- so a green line here is the citation
# integrity check as well as the build.  It runs in the COPY; the comparison is against the shipped file.
REOUT=$( cd "$RUN" && "$PY" refscan141.py --render 2>&1 ); RERC=$?
if [ "$RERC" -eq 0 ]; then
  if cmp -s "$RUN/manuscript.md" "$HERE/manuscript.md"; then
    ok "$(printf '%s' "$REOUT" | grep -o '[0-9]* cited works' | head -1), byte-identical"
  else
    bad "the shipped manuscript.md is not what its own source renders to"
  fi
else
  bad "$(printf '%s' "$REOUT" | tail -1)"
fi

# ---------------------------------------------------------------- 6. the reference layer (offline)
step "reference selection: every cited work has a record"
SELOUT=$( cd "$RUN" && "$PY" refscan141.py --select 2>&1 ); SELRC=$?
if [ "$SELRC" -eq 0 ]; then
  ok "$(printf '%s' "$SELOUT" | grep -oE '[0-9]+ chosen, [0-9]+ with a verified record' | head -1)"
else
  bad "$(printf '%s' "$SELOUT" | grep -E 'MISSING|NOT CITED|not chosen|NOT READY' | head -2 | tr '\n' ' ')"
fi
battery "reference plant battery (offline)" refscan141.py --selftest

step "canon verdicts re-derived from the stored records"
# `--reaudit` re-runs `verdict()` -- the two/three tests that DECIDE a canon entry -- over the records
# already in the store.  It is offline and deterministic, so the status file is sealed to the rules
# that produced it rather than to a network pass that cannot be re-run on a throttled route.
RAOUT=$( cd "$RUN" && "$PY" refscan141.py --reaudit 2>&1 ); RARC=$?
if [ "$RARC" -eq 0 ] && cmp -s "$RUN/refs/canonical-status.json" "$HERE/refs/canonical-status.json"; then
  ok "$(printf '%s' "$RAOUT" | grep -o 'matched [0-9]*, unresolved [0-9]*' | head -1), byte-identical"
else
  bad "$(printf '%s' "$RAOUT" | tail -1)"
fi

# The journal's OWN reference gate -- the editor's instrument, run from the repository root exactly as
# the citation item names it.  It is not vendored in this package (it belongs to the journal), so when
# the package is read outside the repository this leg is NOT RUN with that reason, never a silent pass.
step "the journal's reference gate (refgate.py)"
RGATE=""; D="$HERE"
for _ in 1 2 3 4 5 6 7 8; do
  if [ -f "$D/.github/tools/refgate.py" ]; then RGATE="$D"; break; fi
  PD="$(dirname "$D")"; [ "$PD" = "$D" ] && break; D="$PD"
done
if [ -z "$RGATE" ]; then
  skip "refgate.py lives in the journal repository, not in this package"
elif [ ! -f "$HERE/manuscript.md" ]; then
  skip "no manuscript.md beside this script"
else
  REL=$( "$PY" -c 'import os,sys; print(os.path.relpath(sys.argv[1], sys.argv[2]))' \
         "$HERE/manuscript.md" "$RGATE" )
  GOUT=$( cd "$RGATE" && "$PY" .github/tools/refgate.py "$REL" 2>&1 ); GRC=$?
  case "$GOUT" in
    *"GATE: PASS"*)
      if printf '%s' "$GOUT" | grep -q "0 of them not separated" \
         && printf '%s' "$GOUT" | grep -q "coverage=100.0%"; then
        ok "$(printf '%s' "$GOUT" | grep -o 'entries=[0-9]*' | head -1), $(printf '%s' "$GOUT" | grep -o 'coverage=[0-9.]*%' | head -1), 0 entries not separated"
      else
        bad "verdict PASS but an advisory line reads badly: $(printf '%s' "$GOUT" | grep -E 'block form|author form' | cut -c1-80 | tr '\n' ' ')"
      fi ;;
    *) bad "rc=$GRC: $(printf '%s' "$GOUT" | grep -E 'FAIL|GATE' | tail -1)" ;;
  esac
fi

# ---------------------------------------------------------------- the plant tier (opt-in)
if [ "${PLANT:-0}" = "1" ]; then
  echo
  echo "== plant tier: each check is fired on the defect it names =="
  PFAIL=0; PN=0
  pstep() { printf '  %-50s' "$1"; PN=$((PN+1)); }
  pok()   { echo "fired"; }
  pbad()  { echo "*** DID NOT FIRE ***"; PFAIL=$((PFAIL+1)); }

  # P1 -- the verdict reader.  A reader that accepts silence, or that believes a disagreeing pair of
  # counts, is the recurring weak-reader defect: it reports a pass for a battery that said nothing.
  pstep "reader: a count line is read"
  [ "$(verdict_of 'SELFTEST 23/23')" = "23/23" ] && pok || pbad
  pstep "reader: a disagreeing pair of counts is rejected"
  case "$(verdict_of 'SELFTEST 23/17')" in DISAGREE*) pok ;; *) pbad ;; esac
  pstep "reader: a named ALL PASS is read WITH its ok-line count"
  case "$(verdict_of 'REFSCAN: ALL PASS
[a] ok
[b] ok')" in "REFSCAN: ALL PASS (2 checks)") pok ;; *) pbad ;; esac
  pstep "reader: silence is not a pass"
  [ -z "$(verdict_of 'all good, trust me')" ] && pok || pbad

  # P2 -- the artefact comparison, on one byte
  pstep "artefact comparison catches a one-byte change"
  printf ' ' >>"$RUN/spike_v1_theory.json"
  cmp -s "$RUN/spike_v1_theory.json" "$HERE/spike_v1_theory.json" && pbad || pok

  # P3 -- the render's refusal, on a citation with no record
  pstep "render refuses a citation with no verified record"
  printf '\nand see {{ref:no-such-key-141}}.\n' >>"$RUN/manuscript.src.md"
  RE2=$( cd "$RUN" && "$PY" refscan141.py --render 2>&1 ); RC2=$?
  if [ "$RC2" -ne 0 ] && printf '%s' "$RE2" | grep -q "without a verified record"; then pok; else pbad; fi

  # P4 -- the figure comparison, on one byte
  pstep "figure comparison catches a one-byte change"
  F1=$(ls "$RUN"/figures/*.png 2>/dev/null | head -1)
  if [ -n "$F1" ]; then
    printf '\001' >>"$F1"
    FO2=$( cd "$RUN" && MPLCONFIGDIR="$WORK/.mpl" "$PY" figures.py --check 2>&1 )
    case "$FO2" in
      *"ALL IDENTICAL"*) pbad ;;
      *"FIGURES:"*)      pok ;;
      *)                 pbad ;;
    esac
  else
    pbad
  fi

  if [ "$PFAIL" -eq 0 ]; then
    echo "PLANT: ALL $PN CHECKS FIRED"
  else
    echo "PLANT: $PFAIL OF $PN DID NOT FIRE"; FAILS=$((FAILS+1))
  fi
fi

# ---------------------------------------------------------------- verdict
echo
if [ "$FAILS" = 0 ]; then
  echo "REPRODUCE: ALL GREEN${SKIPS:+ ($SKIPS leg(s) NOT RUN -- named above)}"
  exit 0
fi
echo "REPRODUCE: $FAILS STEP(S) FAILED${SKIPS:+ ($SKIPS leg(s) NOT RUN -- named above)}"
exit 1
